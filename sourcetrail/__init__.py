"""SourceTrail: go from a claim back to the evidence in your own files."""
from .db import Library
from .trace import trace, Evidence, Result

__version__ = "0.1.0"
__all__ = ["Library", "trace", "Evidence", "Result", "__version__"]
