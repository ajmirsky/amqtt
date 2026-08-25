from dataclasses import dataclass, is_dataclass
from typing import Any, Generic, TypeVar, cast

from amqtt.contexts import Action, BaseContext, BrokerConfig
from amqtt.session import Session

C = TypeVar("C", bound=BaseContext)


class BasePlugin(Generic[C]):
    """The base from which all plugins should inherit.

    Type Parameters
    ---------------
    C:
        A BaseContext: either BrokerContext or ClientContext, depending on plugin usage

    Attributes
    ----------
    context (C):
        Information about the environment in which this plugin is executed. Modifying
        the broker or client state should happen through methods available here.

    config (self.Config):
        An instance of the Config dataclass defined by the plugin (or an empty dataclass, if not
        defined).

    """

    def __init__(self, context: C) -> None:
        self.context: C = context
        # since the PluginManager will hydrate the config from a plugin's `Config` class, this is a safe cast
        self.config = cast("self.Config", context.config)  # type: ignore[name-defined]

    @dataclass
    class Config:
        """Override to define the configuration and defaults for plugin."""

    async def close(self) -> None:
        """Override if plugin needs to clean up resources upon shutdown."""


class BaseTopicPlugin(BasePlugin[BaseContext]):
    """Base class for topic plugins."""

    def __init__(self, context: BaseContext) -> None:
        super().__init__(context)

    async def topic_filtering(
        self, *, session: Session | None = None, topic: str | None = None, action: Action | None = None
    ) -> bool | None:
        """Logic for filtering out topics.

        Args:
            session: amqtt.session.Session
            topic: str
            action: amqtt.broker.Action

        Returns:
            bool: `True` if topic is allowed, `False` otherwise. `None` if it can't be determined

        """
        return None


class BaseAuthPlugin(BasePlugin[BaseContext]):
    """Base class for authentication plugins."""

    def __init__(self, context: BaseContext) -> None:
        super().__init__(context)

    async def authenticate(self, *, session: Session) -> bool | None:
        """Logic for session authentication.

        Args:
            session: amqtt.session.Session

        Returns:
            - `True` if user is authentication succeed, `False` if user authentication fails
            - `None` if authentication can't be achieved (then plugin result is then ignored)

        """
        return None
