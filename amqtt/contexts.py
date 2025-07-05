import warnings
from dataclasses import field, dataclass
from enum import Enum, StrEnum
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    import asyncio


class BaseContext:
    def __init__(self) -> None:
        self.loop: asyncio.AbstractEventLoop | None = None
        self.logger: logging.Logger = logger
        self.config: dict[str, Any] | None = None


class Action(Enum):
    """Actions issued by the broker."""

    SUBSCRIBE = "subscribe"
    PUBLISH = "publish"


class ListenerType(StrEnum):
    TCP = 'tcp'
    WS = 'ws'


@dataclass
class ListenerConfig:
    type: ListenerType = field(default=ListenerType.TCP)
    bind: str | None = None
    max_connections: int | None = field(default=0)
    ssl: bool = field(default=False)
    cafile: str | Path | None = None
    capath: str | Path | None = None
    cadata: str | Path | None = None
    certfile: str | Path | None = None
    keyfile: str | Path | None = None


@dataclass
class BrokerConfig:
    listeners: dict[str, ListenerConfig] = field(default_factory=dict)
    sys_interval: int | None = None
    plugins: dict[str, dict[str, Any]] | list[dict[str, Any]] = field(default_factory=dict)
    auth: dict[str, Any] | None = None
    topic_check: dict[str, Any] | None = None

    def __post__init__(self) -> None:
        if self.sys_interval is not None:
            warnings.warn("sys_interval is deprecated, use 'plugins' to define configuration", DeprecationWarning, stacklevel=2)

        if self.auth is not None or self.topic_check is not None:
            

        if isinstance(self.plugins, list):
            _plugins = {}
            for plugin in self.plugins:
                _plugins |= plugin
            self.plugins = _plugins