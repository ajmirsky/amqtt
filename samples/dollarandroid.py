"""dollarandroid.py

A $SYS plugin to provide broker statistics for platforms, like android, that don't support `psutil`

Both calls are on the *current* process (no pid passed in), so we only
ever read /proc/self/*, which stays readable on non-rooted Android/Termux
even when /proc/<other_pid>/* is restricted. No C extension, no build
step, works anywhere /proc is mounted (i.e. any real Linux, including
Android's kernel).

activate through broker configuration:

```
---
listeners:
   ...
plugins:
  mypackage.myplugins.dollarandroid.AndroidSysPlugin:
    sys_interval: 20
```
"""
import asyncio
from collections import defaultdict
from dataclasses import dataclass
import os
import time
from typing import Any
import warnings

from amqtt.broker import BrokerContext
from amqtt.codecs_amqtt import float_to_bytes_str, int_to_bytes_str
from amqtt.plugins.base import BasePlugin


def val_to_bytes_str(value: Any) -> bytes:
    """Convert an int, float or string to byte string."""
    match value:
        case int():
            return int_to_bytes_str(value)
        case float():
            return float_to_bytes_str(value)
        case str():
            return value.encode("utf-8")
        case _:
            msg = f"Unsupported type {type(value)}"
            raise NotImplementedError(msg)


class MemInfo:
    """Corollary to psutil's pmem/pfullmem namedtuple. Only .rss is populated."""

    __slots__ = ("rss",)

    def __init__(self, rss_bytes: int) -> None:
        self.rss = rss_bytes

    def __repr__(self) -> str:
        return f"MemInfo(rss={self.rss})"


class Process:
    """Corollary to psutil.Process, current-process only."""

    def __init__(self, pid: int | None = None) -> None:
        self.pid: int = pid if pid is not None else os.getpid()
        self._last_cpu_time: float | None = None
        self._last_wall_time: float | None = None
        self._clk_tck: int | None = None

        if "SC_CLK_TCK" in os.sysconf_names:
            self._clk_tck = os.sysconf("SC_CLK_TCK")

    def _read_cpu_times(self, clk_tck: int) -> tuple[float, float]:
        """Return (utime, stime) in seconds, read from /proc/<pid>/stat."""
        with open(f"/proc/{self.pid}/stat", encoding="utf-8", errors="replace") as f:
            raw = f.read()
        # comm field is in parens and may itself contain ')' or spaces,
        # so split from the *last* ')' rather than by naive whitespace split.
        rparen = raw.rfind(")")
        fields = raw[rparen + 2:].split()
        # fields[0] == state (field 3 overall); utime is field 14, stime field 15
        utime_ticks = int(fields[11])
        stime_ticks = int(fields[12]) or 0
        return float(utime_ticks / clk_tck), float(stime_ticks / clk_tck)

    def cpu_percent(self) -> float:
        """Mirrors psutil's non-blocking usage pattern (interval=0 / None):
        compares CPU time consumed since the previous call against wall
        time elapsed since the previous call. First call returns 0.0,
        exactly like real psutil ("meaningless value ... supposed to
        ignore" per psutil's own docs).
        """
        clk_tck = self._clk_tck
        if clk_tck is None:
            return 0.0

        cpu_time = sum(self._read_cpu_times(clk_tck))
        now = time.monotonic()

        last_cpu_time = self._last_cpu_time
        last_wall_time = self._last_wall_time
        if last_cpu_time is None or last_wall_time is None:
            self._last_cpu_time = cpu_time
            self._last_wall_time = now
            return 0.0

        elapsed_wall = now - last_wall_time
        elapsed_cpu = cpu_time - last_cpu_time

        self._last_cpu_time = cpu_time
        self._last_wall_time = now

        if elapsed_wall <= 0:
            return 0.0

        return (elapsed_cpu / elapsed_wall) * 100.0

    def memory_full_info(self) -> MemInfo:
        """Returns an object with a .rss attribute in bytes, read from
        /proc/<pid>/status (VmRSS). Real psutil's memory_full_info()
        also exposes uss/pss/etc via /proc/<pid>/smaps, which amqtt
        doesn't use and which is more likely to be permission-restricted
        on Android -- so we deliberately don't touch smaps here.
        """
        rss_kb = 0
        with open(f"/proc/{self.pid}/status", encoding="utf-8", errors="replace") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    # format: "VmRSS:\t   12345 kB"
                    rss_kb = int(line.split()[1])
                    break
        return MemInfo(rss_bytes=rss_kb * 1024)


DOLLAR_SYS_ROOT = "$SYS/android/"  # or "$SYS/broker/"
CPU_USAGE_LAST = "cpu_usage_last"
CPU_USAGE_MAXIMUM = "cpu_usage_maximum"
MEMORY_USAGE_LAST = "memory_usage_last"
MEMORY_USAGE_MAXIMUM = "memory_usage_maximum"


class AndroidSysPlugin(BasePlugin[BrokerContext]):
    def __init__(self, context: BrokerContext) -> None:
        super().__init__(context)

        # Broker statistics initialization
        self.stats: defaultdict[str, float] = defaultdict(float)
        self.process_handle = Process()
        self.sys_broadcast_task: asyncio.Handle | None = None
        self.sys_interval = self._get_config_option("sys-interval", 0)
        self.broadcast_tasks: set[asyncio.Future[None]] = set()

    async def on_broker_pre_start(self) -> None:
        self.stats.clear()

    async def on_broker_post_start(self) -> None:
        self.process_handle = Process()

        self.context.logger.debug(f"Setup $SYS broadcasting every {self.sys_interval} seconds")
        if not self.context.loop or self.sys_interval <= 0:
            warnings.warn("AndroidSysPlugin: $SYS broadcasting disabled or config has invalid interval")
            return

        self.sys_broadcast_task = self.context.loop.call_later(self.sys_interval, self.broadcast_dollar_sys_topics)

    def broadcast_dollar_sys_topics(self) -> None:
        """Gather current states of cpu and memory and broadcast $SYS topics updates."""
        cpu_usage = self.process_handle.cpu_percent()
        mem_usage = self.process_handle.memory_full_info().rss / (1024**2)

        self.stats[CPU_USAGE_MAXIMUM] = max(self.stats[CPU_USAGE_MAXIMUM], cpu_usage)
        self.stats[MEMORY_USAGE_MAXIMUM] = max(self.stats[MEMORY_USAGE_MAXIMUM], mem_usage)
        self.stats[CPU_USAGE_LAST] = cpu_usage
        self.stats[MEMORY_USAGE_LAST] = mem_usage

        if not self.context.loop or self.sys_interval <= 0:
            return

        # create a task to broadcast each stat
        for stat_name, stat_value in self.stats.items():
            data: bytes = val_to_bytes_str(stat_value)
            task = self.context.loop.create_task(self.broadcast_sys_topic(DOLLAR_SYS_ROOT + stat_name, data))
            self.broadcast_tasks.add(task)
            task.add_done_callback(self.cleanup_broadcast_task)

        # reschedule task for next execution
        self.sys_broadcast_task = self.context.loop.call_later(self.sys_interval, self.broadcast_dollar_sys_topics)

    async def broadcast_sys_topic(self, topic_basename: str, data: bytes) -> None:
        """Broadcast a system topic."""
        await self.context.broadcast_message(topic_basename, data)

    def cleanup_broadcast_task(self, task: asyncio.Future[None]) -> None:
        """Clean up a broadcast task after it's done."""
        self.broadcast_tasks.discard(task)
        try:
            task.result()
        except asyncio.CancelledError:
            pass
        # if a task fails, don't want it to cause the broker to fail
        except Exception:  # pylint: disable=W0718
            self.context.logger.exception(f"$SYS broadcast task failed and will be skipped: {task}")

    async def on_broker_pre_shutdown(self) -> None:
        """Stop $SYS topics broadcasting."""
        if self.sys_broadcast_task:
            self.sys_broadcast_task.cancel()
        for task in self.broadcast_tasks:
            task.cancel()
        await asyncio.gather(*self.broadcast_tasks, return_exceptions=True)
        self.broadcast_tasks.clear()

    @dataclass
    class Config:
        """Configuration struct for AndroidSysPlugin."""

        sys_interval: int = 20
        """samping and sending interval in seconds"""
