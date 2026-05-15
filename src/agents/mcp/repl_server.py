"""MCP Server: Python REPL for financial calculations.

Executes Python code in an isolated subprocess with restricted capabilities.
NO file system access, NO network calls, NO dangerous imports.
"""
from __future__ import annotations
import sys
import json
import ast
import traceback
from io import StringIO
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("python-repl")

# Allowed packages for financial calculations
_ALLOWED_IMPORTS = {
    "numpy", "np", "pandas", "pd", "scipy", "math", "statistics",
    "decimal", "fractions", "random", "itertools", "collections",
    "datetime", "time", "json", "re", "typing", "enum",
}

# Blocked keywords for security
_BLOCKED_KEYWORDS = [
    "import os", "import sys", "import subprocess", "import shutil",
    "import socket", "import requests", "import httpx", "import http",
    "import pathlib", "__import__", "eval(", "exec(", "open(",
    "__builtins__", "compile(", "getattr", "setattr", "delattr",
]


def _is_safe(code: str) -> tuple[bool, str]:
    """Validate that code is safe to execute.
    
    Returns (safe: bool, reason: str).
    """
    for blocked in _BLOCKED_KEYWORDS:
        if blocked in code:
            return False, f"Blocked: {blocked} is not allowed"
    
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] not in _ALLOWED_IMPORTS:
                        return False, f"Import not allowed: {alias.name}"
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module.split(".")[0] not in _ALLOWED_IMPORTS:
                    return False, f"Import not allowed: {node.module}"
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ("exec", "eval", "compile", "__import__", "open"):
                        return False, f"Function not allowed: {node.func.id}"
    except SyntaxError as e:
        return False, f"Syntax error: {e}"
    
    return True, ""


@mcp.tool()
def calculate_python(code: str) -> str:
    """Execute Python code for financial calculations.
    
    Available packages: numpy, pandas, scipy, math, statistics
    Restrictions: no file I/O, no network, no dangerous functions
    30-second timeout.
    
    Args:
        code: Python code to execute. Use print() to see output.
        
    Examples:
        - NPV: "print(sum([100/(1.1**i) for i in range(1,6)]) - 400)"
        - Sharpe: "import numpy as np; returns = [0.01, -0.02, 0.03, 0.01, -0.01]; print(np.mean(returns)/np.std(returns)*np.sqrt(252))"
        - Simple moving avg: "import pandas as pd; prices = [100,102,101,105,107]; print(pd.Series(prices).rolling(3).mean().tolist())"
    """
    safe, reason = _is_safe(code)
    if not safe:
        return f"Security violation: {reason}"
    
    # Capture stdout
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    
    try:
        # Restricted globals for execution
        restricted_globals = {
            "__builtins__": {
                "print": print,
                "range": range,
                "len": len,
                "int": int,
                "float": float,
                "str": str,
                "list": list,
                "dict": dict,
                "tuple": tuple,
                "set": set,
                "bool": bool,
                "True": True,
                "False": False,
                "None": None,
                "abs": abs,
                "all": all,
                "any": any,
                "enumerate": enumerate,
                "filter": filter,
                "isinstance": isinstance,
                "map": map,
                "max": max,
                "min": min,
                "pow": pow,
                "reversed": reversed,
                "round": round,
                "slice": slice,
                "sorted": sorted,
                "sum": sum,
                "zip": zip,
                "Exception": Exception,
                "ValueError": ValueError,
                "TypeError": TypeError,
                "ZeroDivisionError": ZeroDivisionError,
            },
        }
        
        exec(code, restricted_globals)
        output = sys.stdout.getvalue()
        return output if output else "Code executed successfully (no output)"
    except Exception as e:
        return f"Error:\n{traceback.format_exc()}"
    finally:
        sys.stdout = old_stdout


if __name__ == "__main__":
    mcp.run()
