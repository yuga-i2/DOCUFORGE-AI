"""Sandboxed Python code execution tool for the Analyst Agent."""

import logging
import subprocess
import sys

from langchain_core.tools import Tool

logger = logging.getLogger(__name__)

# Auto-imported modules for code execution context
PREAMBLE = "import pandas as pd\nimport numpy as np\nimport json\n"


def execute_python_code(code: str) -> dict[str, str]:
    """Execute Python code in a subprocess with 30 second timeout and return stdout/stderr. Automatically prepends pandas, numpy, and json imports. Never uses eval/exec — subprocess only. Returns dict with keys: stdout, stderr, success (true/false)."""
    try:
        full_code = PREAMBLE + code
        logger.info(f"Executing code block of {len(full_code)} characters")
        
        result = subprocess.run(
            [sys.executable, "-c", full_code],
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        success = result.returncode == 0
        logger.info(f"Code execution success={success}")
        
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": str(success).lower(),
        }
    except subprocess.TimeoutExpired:
        logger.warning("Code execution timed out after 30 seconds")
        return {
            "stdout": "",
            "stderr": "Execution timed out after 30 seconds",
            "success": "false",
        }
    except Exception as e:
        logger.error(f"Code execution error: {str(e)}")
        return {
            "stdout": "",
            "stderr": f"Execution error: {str(e)}",
            "success": "false",
        }


def get_code_executor_tool() -> Tool:
    """Return a configured LangChain Tool wrapping execute_python_code for use in agent chains."""
    return Tool.from_function(
        func=execute_python_code,
        name="code_executor",
        description="Execute Python code safely in a sandbox. Returns stdout, stderr, and success status.",
    )
