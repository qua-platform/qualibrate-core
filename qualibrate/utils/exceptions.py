import types
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, cast

if TYPE_CHECKING:
    from qualibrate.q_runnnable import (
        CreateParametersType,
        QRunnable,
        RunParametersType,
    )


class StopInspection(Exception):
    def __init__(
        self,
        *args: Any,
        instance: "QRunnable[CreateParametersType, RunParametersType]",
    ):
        super().__init__(*args, instance)
        self.instance = instance


class TargetsFieldNotExist(AttributeError):
    pass


def reverse_tb(traceback: types.TracebackType) -> types.TracebackType:
    prev = None
    tb: Optional[types.TracebackType] = traceback
    while tb:
        next_tb = tb.tb_next
        tb = types.TracebackType(prev, tb.tb_frame, tb.tb_lasti, tb.tb_lineno)
        prev = tb
        tb = next_tb
    return cast(types.TracebackType, prev)


def skip_exception_frames(
    ex: Exception,
    skip_func_name: str,
    skip_filename: str,
    count: int = 1,
) -> Exception:
    tb = ex.__traceback__
    new_tb = None

    while tb is not None:
        frame = tb.tb_frame
        code_name = frame.f_code.co_name
        code_filename = Path(frame.f_code.co_filename).name

        if code_name != skip_func_name or code_filename != skip_filename:
            new_tb = types.TracebackType(
                tb_next=new_tb,
                tb_frame=frame,
                tb_lasti=tb.tb_lasti,
                tb_lineno=tb.tb_lineno,
            )
        else:
            if count <= 0:
                raise ValueError("Can't skip exception lines") from ex
            # 1 frame will be skipped after else block
            count = count - 1
            while count > 0 and tb:
                tb = tb.tb_next
                count -= 1
        if tb is not None:
            tb = tb.tb_next

    if new_tb is not None:
        ex.__traceback__ = reverse_tb(new_tb)
    return ex
