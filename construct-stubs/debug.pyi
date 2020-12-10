from typing import Optional, Callable, Any
from construct import Construct, Subconstruct
from construct.core import Context

ContextLambda = Callable[[Context], Any]

class Probe(Construct[None, None]):
    def __init__(
        self, into: Optional[ContextLambda] = ..., lookahead: int = ...
    ) -> None: ...

class Debugger(Subconstruct[None, None]): ...
