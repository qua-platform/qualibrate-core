import inspect
from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, Optional, Union

from typing_extensions import TypeAlias

from qualibrate.runnables.run_action.action import (
    Action,
    ActionCallableType,
    ActionReturnType,
)
from qualibrate.runnables.run_action.utils import (
    get_defined_in_frame_names,
    get_frame_for_keeping_names_from_manager,
)
from qualibrate.utils.logger_m import logger

if TYPE_CHECKING:
    from qualibrate.qualibration_node import QualibrationNode


ActionDecoratorType: TypeAlias = Union[
    ActionCallableType, Callable[..., ActionCallableType]
]


class ActionManager:
    """
    Manages run actions for a QualibrationNode. It holds an exit flag
    which, once set, prevents further actions from running.
    """

    def __init__(self) -> None:
        self.actions: dict[str, Action] = {}
        stack = inspect.stack()
        frame_for_names = get_frame_for_keeping_names_from_manager(stack)
        self.predefined_names = get_defined_in_frame_names(frame_for_names)

    def run_action(
        self,
        action_name: str,
        node: "QualibrationNode[Any, Any]",
        *args: Any,
        **kwargs: Any,
    ) -> Optional[ActionReturnType]:
        if action := self.actions.get(action_name):
            return action.execute_run_action(node, *args, **kwargs)
        logger.warning(f"Can't run action {action_name} of node {node}")
        return None

    def register_action(
        self,
        node: "QualibrationNode[Any, Any]",
        func: Optional[ActionCallableType] = None,
        *,
        skip_if: bool = False,
    ) -> ActionDecoratorType:
        """
        Returns a decorator that creates an Action instance and executes
        it immediately.

        Supports usage both without parentheses:

            @node.run_action
            def action(node):
                ...

        and with parentheses:

            @node.run_action(skip_if=True)
            def action(node):
                ...

        Behavior:
          - If skip_if is True, the function is not run.
        """

        def decorator(
            f: ActionCallableType,
        ) -> ActionCallableType:
            nonlocal node
            action = Action(f, self)
            node._action_manager.actions[f.__name__] = action

            @wraps(f)
            def wrapper(
                *args: Any, **kwargs: Any
            ) -> Optional[ActionReturnType]:
                return action.execute_run_action(node, *args, **kwargs)

            if skip_if:
                # Skip this action; do not set exit even if exit=True.
                return wrapper
            wrapper()
            return wrapper

        return decorator if func is None else decorator(func)
