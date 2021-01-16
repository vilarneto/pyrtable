from typing import Optional

from .base import *


_default_context: Optional[BaseContext] = None


def set_default_context(context: BaseContext):
    global _default_context
    _default_context = context


def get_default_context() -> BaseContext:
    global _default_context

    if _default_context is None:
        set_default_context(BaseContext())

    return _default_context
