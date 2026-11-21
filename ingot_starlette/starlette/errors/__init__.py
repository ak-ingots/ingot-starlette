"""The errors: the policies of the exceptions, as Starlette handles them."""

__all__ = (
    "BaseStarletteErrorPolicy",
    "BaseStarletteProblemRenderer",
    "BaseStaticStarletteErrorPolicy",
    "HttpStarletteErrorPolicy",
    "InternalStarletteErrorPolicy",
    "StarletteErrorsUnit",
    "StarletteHtmlProblemRenderer",
    "StarletteJsonProblemRenderer",
    "StarletteProblem",
    "encode_problem",
)

import typing as t

from ingots.puer import Slot, Unit

from .data import StarletteProblem
from .policies import (
    BaseStarletteErrorPolicy,
    BaseStaticStarletteErrorPolicy,
    HttpStarletteErrorPolicy,
    InternalStarletteErrorPolicy,
    encode_problem,
)
from .renderers import (
    BaseStarletteProblemRenderer,
    StarletteHtmlProblemRenderer,
    StarletteJsonProblemRenderer,
)

if t.TYPE_CHECKING:
    from starlette.requests import HTTPConnection
    from starlette.responses import Response
    from starlette.types import ExceptionHandler


class StarletteErrorsUnit(Unit):
    """
    The policies of the project, each in a slot of its own, shared by the
    subtrees: :attr:`internal` takes every exception no other policy takes,
    :attr:`http` the ``HTTPException`` of Starlette. An exception class has
    one policy::

        class AppStarletteErrorsUnit(StarletteErrorsUnit):
            insufficient_funds = Slot(InsufficientFundsPolicy)

    A subtree takes the handlers of Starlette of every policy with its own
    renderer, :meth:`get_exception_handlers`: the problem of an exception is
    the policy's, its form the subtree's, JSON or HTML.

    A failure after a response has started, of a stream, Starlette does not
    handle: the endpoint encodes it in its band by :meth:`encode`.
    """

    internal = Slot(InternalStarletteErrorPolicy)
    http = Slot(HttpStarletteErrorPolicy)

    _policies_by_exception: t.ClassVar[dict[type[Exception], str]]

    @t.override
    @classmethod
    def __init_subclass__(cls, **kwargs: t.Any) -> None:
        super().__init_subclass__(**kwargs)
        index_policies(cls)

    @t.final
    def get_exception_handlers(
        self, renderer: BaseStarletteProblemRenderer
    ) -> "dict[t.Any, ExceptionHandler]":
        """The handlers of Starlette, by exception class: a policy each, rendered."""
        kind: t.Any = BaseStarletteErrorPolicy  # abstract
        handlers: "dict[t.Any, ExceptionHandler]" = {}
        for exception, name in self._policies_by_exception.items():
            policy: BaseStarletteErrorPolicy = self.slots_find_entity(name, kind)
            # one handler of both, a request and a WebSocket: Starlette types two
            handler = ProblemHandler(policy, renderer)
            handlers[exception] = t.cast("ExceptionHandler", handler)
        return handlers

    @t.final
    def find_policy(self, error: Exception) -> BaseStarletteErrorPolicy:
        """The policy of an exception, by the classes of its MRO."""
        kind: t.Any = BaseStarletteErrorPolicy  # abstract
        for klass in type(error).__mro__:
            if name := self._policies_by_exception.get(klass):
                return t.cast(
                    BaseStarletteErrorPolicy, self.slots_find_entity(name, kind)
                )
        raise AssertionError(f"{self!r}: no policy of Exception")  # pragma: no cover

    @t.final
    def encode(
        self, error: Exception, connection: "HTTPConnection"
    ) -> StarletteProblem:
        """The problem of an exception, by its policy, logged."""
        return self.find_policy(error).report(error, connection)


class ProblemHandler:
    """Internal: a handler of Starlette, a policy and the renderer of a subtree."""

    def __init__(
        self, policy: BaseStarletteErrorPolicy, renderer: BaseStarletteProblemRenderer
    ) -> None:
        self._policy = policy
        self._renderer = renderer

    async def __call__(
        self, connection: "HTTPConnection", error: Exception
    ) -> "Response | None":
        problem = self._policy.report(error, connection)
        return await self._renderer.render(problem, connection)


def index_policies(cls: type[StarletteErrorsUnit]) -> None:
    """Internal, run when the class is created: the policies by exception."""
    by_exception: dict[type[Exception], str] = {}
    kind: t.Any = BaseStarletteErrorPolicy  # abstract
    for name, slot in cls.slots_iter(kind):
        owner = by_exception.setdefault(slot.cls.EXCEPTION, name)
        if owner != name:
            raise TypeError(
                f"{cls.__qualname__}: {slot.cls.EXCEPTION.__qualname__} has both "
                f"{owner} and {name}"
            )
    cls._policies_by_exception = by_exception


index_policies(StarletteErrorsUnit)  # __init_subclass__ runs for the subclasses only
