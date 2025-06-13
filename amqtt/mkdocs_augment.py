from enum import Enum
from typing import Any

import mkdocs


def isenum(obj: Any) -> bool:
    return isinstance(obj, Enum)


class MyPluginConfig(mkdocs.config.base.Config):
    foo = mkdocs.config.config_options.Type(str, default="a default value")
    bar = mkdocs.config.config_options.Type(int, default=0)
    baz = mkdocs.config.config_options.Type(bool, default=True)

class MyPlugin(mkdocs.plugins.BasePlugin[MyPluginConfig]):

    config_scheme = (
        ("foo", mkdocs.config.config_options.Type(str, default="a default value")),
        ("bar", mkdocs.config.config_options.Type(int, default=0)),
        ("baz", mkdocs.config.config_options.Type(bool, default=True))
    )

    def on_pre_build(self, config, **kwargs):
        handler = config["plugins"]["mkdocstrings"]._handlers["python"]
        original_render = handler.renderer.render

        def render_with_enum_values(data, *args, **kwargs):
            if isenum(data["obj"]):
                enum_members = inspect.getmembers(data["obj"], lambda m: isinstance(m, data["obj"]))
                value_lines = [f"- **{k}** = `{v.value!r}`" for k, v in enum_members if not k.startswith("_")]
                if "docstring" in data:
                    data["docstring"]["summary"] += "\n\n**Enum values:**\n" + "\n".join(value_lines)
            return original_render(data, *args, **kwargs)

        handler.renderer.render = render_with_enum_values
        return config
