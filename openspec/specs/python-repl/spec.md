# Python REPL

## Purpose
Sandboxed Python execution MCP server for financial calculations. Execution runs in an isolated subprocess with strict security constraints.

## Requirements

### Requirement: Safe Python Execution
The system SHALL execute Python code in an isolated subprocess (NOT in-process exec()). numpy, pandas, and scipy SHALL be available. File system access, network calls, and imports beyond allowed packages SHALL be blocked.

| # | Constraint | Value |
|---|-----------|-------|
| R1.1 | Isolation | Subprocess (not exec()) |
| R1.2 | Allowed packages | numpy, pandas, scipy |
| R1.3 | Supported calculations | NPV, IRR, Sharpe, VaR, beta |
| R1.4 | Execution timeout | 30 seconds |
| R1.5 | Blocked | Filesystem, network, unlisted imports |
| R1.6 | Error surfacing | All errors returned to user |

#### Scenario: Execute NPV calculation via tool
- GIVEN Python REPL MCP server running
- WHEN `calculate_npv(rate=0.05, cashflows=[-1000, 200, 300, 400, 500])` is called
- THEN SHALL execute np.npv() in sandbox subprocess
- AND SHALL return correct numeric NPV result

#### Scenario: Execute custom Python via generic tool
- GIVEN `execute_python("import numpy as np; np.mean([1, 2, 3, 4, 5])")` is called
- WHEN code runs in sandbox subprocess
- THEN stdout SHALL return "3.0"

#### Scenario: Timeout kills runaway execution
- GIVEN Python code containing `while True: pass`
- WHEN 30 seconds elapse
- THEN subprocess SHALL be forcibly terminated
- AND SHALL return "Execution timed out after 30s"

#### Scenario: Blocked filesystem access
- GIVEN `execute_python("open('/etc/passwd').read()")` is called
- WHEN sandbox restricts filesystem operations
- THEN SHALL return error indicating operation not permitted
- AND SHALL NOT expose any filesystem content

#### Scenario: Blocked network access
- GIVEN `execute_python("import requests; requests.get('http://evil.com')")` is called
- WHEN sandbox blocks network calls OR import is not in allowed list
- THEN SHALL return error: network access prohibited or import not allowed

#### Scenario: Import restriction enforcement
- GIVEN `execute_python("import os; os.system('whoami')")` is called
- WHEN `os` is not in allowed packages list
- THEN SHALL return error: "ImportError: module 'os' is not permitted"
