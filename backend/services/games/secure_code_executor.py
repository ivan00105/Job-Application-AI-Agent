"""
Secure code execution service with improved security measures.
This is an improved version with better security, but still not fully sandboxed.
For production, use Docker-based execution.
"""
import subprocess
import tempfile
import os
import logging
import re
import ast
from typing import Dict, Any, List, Optional
import json

logger = logging.getLogger(__name__)

# Dangerous imports that should be blocked
DANGEROUS_IMPORTS = {
    'os', 'sys', 'subprocess', 'shutil', 'socket', 'urllib', 'requests',
    'http', 'ftplib', 'smtplib', 'telnetlib', 'pickle', 'marshal',
    'ctypes', 'multiprocessing', 'threading', 'importlib', 'eval',
    'exec', 'compile', '__import__', 'open', 'file', 'input', 'raw_input'
}

# Dangerous function calls
DANGEROUS_FUNCTIONS = {
    'eval', 'exec', 'compile', '__import__', 'open', 'file',
    'input', 'raw_input', 'execfile', 'reload'
}


class SecureCodeExecutor:
    """
    Improved code executor with security restrictions.
    Still not fully secure - use Docker for production.
    """
    
    def __init__(self, timeout_seconds: int = 10, max_memory_mb: int = 128):
        self.timeout_seconds = timeout_seconds
        self.max_memory_mb = max_memory_mb
    
    def _analyze_code(self, code: str) -> tuple[bool, Optional[str]]:
        """
        Analyze code for dangerous patterns.
        Returns (is_safe, error_message)
        """
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                # Check for dangerous imports
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if alias.name.split('.')[0] in DANGEROUS_IMPORTS:
                                return False, f"Dangerous import detected: {alias.name}"
                    elif isinstance(node, ast.ImportFrom):
                        if node.module and node.module.split('.')[0] in DANGEROUS_IMPORTS:
                            return False, f"Dangerous import detected: {node.module}"
                
                # Check for dangerous function calls
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in DANGEROUS_FUNCTIONS:
                            return False, f"Dangerous function call detected: {node.func.id}"
                    elif isinstance(node.func, ast.Attribute):
                        if node.func.attr in DANGEROUS_FUNCTIONS:
                            return False, f"Dangerous method call detected: {node.func.attr}"
                
                # Check for eval/exec in strings
                if isinstance(node, ast.Str) or isinstance(node, ast.Constant):
                    value = node.s if hasattr(node, 's') else (node.value if isinstance(node.value, str) else '')
                    if any(danger in value.lower() for danger in ['eval(', 'exec(', '__import__']):
                        return False, "Potentially dangerous string pattern detected"
            
            return True, None
            
        except SyntaxError as e:
            # Syntax errors are OK - they'll be caught during execution
            return True, None
        except Exception as e:
            logger.warning(f"Code analysis error: {e}")
            # If analysis fails, be conservative
            return False, f"Code analysis failed: {str(e)}"
    
    async def execute_python(
        self,
        code: str,
        test_cases: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Execute Python code with security restrictions.
        """
        # Step 1: Analyze code for dangerous patterns
        is_safe, error_msg = self._analyze_code(code)
        if not is_safe:
            return {
                "passed": False,
                "test_results": [],
                "total_tests": len(test_cases),
                "passed_tests": 0,
                "error": f"Security violation: {error_msg}",
                "security_blocked": True
            }
        
        results = []
        all_passed = True
        
        for i, test_case in enumerate(test_cases):
            test_input = test_case.get("input", {})
            expected_output = test_case.get("expected_output")
            test_name = test_case.get("name", f"Test {i+1}")
            
            # Create a temporary Python file in a restricted location
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, dir='/tmp') as f:
                # Write the user's code
                f.write(code)
                f.write("\n\n")
                
                # Add test execution code
                f.write("# Test execution\n")
                f.write("import json\n")
                f.write("try:\n")
                
                # Extract function name from code
                function_name = self._extract_function_name(code)
                if not function_name:
                    results.append({
                        "test_name": test_name,
                        "passed": False,
                        "error": "No function found in code. Please define a function.",
                        "input": test_input,
                        "expected": expected_output,
                        "actual": None
                    })
                    all_passed = False
                    os.unlink(f.name)
                    continue
                
                # Build function call
                if isinstance(test_input, dict):
                    args_str = ", ".join([f"{k}={repr(v)}" for k, v in test_input.items()])
                    call_str = f"{function_name}({args_str})"
                    input_var = list(test_input.keys())[0] if test_input else None
                    if input_var:
                        input_value = test_input[input_var]
                        f.write(f"    {input_var} = {repr(input_value)}\n")
                        f.write(f"    {call_str}\n")
                        f.write(f"    print(json.dumps({{'result': {input_var}, 'status': 'success'}}))\n")
                    else:
                        f.write(f"    result = {call_str}\n")
                        f.write(f"    print(json.dumps({{'result': result, 'status': 'success'}}))\n")
                else:
                    args_str = repr(test_input)
                    call_str = f"{function_name}({args_str})"
                    f.write(f"    result = {call_str}\n")
                    f.write(f"    print(json.dumps({{'result': result, 'status': 'success'}}))\n")
                
                f.write("except Exception as e:\n")
                f.write(f"    print(json.dumps({{'error': str(e), 'status': 'error'}}))\n")
                
                temp_file = f.name
            
            try:
                # Execute with restrictions
                # Note: ulimit restrictions would need to be set at OS level
                # For now, we rely on timeout and code analysis
                process = subprocess.run(
                    ["python3", "-u", temp_file],  # -u for unbuffered output
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                    # Run with minimal environment
                    env={
                        "PYTHONIOENCODING": "utf-8",
                        "PYTHONUNBUFFERED": "1",
                        # Remove dangerous environment variables
                        "PATH": "/usr/bin:/bin",
                    },
                    # Run from temp directory
                    cwd=tempfile.gettempdir(),
                    # Set resource limits (if supported)
                    # preexec_fn=self._set_limits  # Unix only
                )
                
                # Parse output
                output = process.stdout.strip()
                error_output = process.stderr.strip()
                
                if error_output:
                    # Filter out security-related errors that might leak info
                    filtered_error = self._filter_error(error_output)
                    results.append({
                        "test_name": test_name,
                        "passed": False,
                        "error": filtered_error,
                        "input": test_input,
                        "expected": expected_output,
                        "actual": None
                    })
                    all_passed = False
                elif output:
                    try:
                        result_data = json.loads(output)
                        if result_data.get("status") == "error":
                            results.append({
                                "test_name": test_name,
                                "passed": False,
                                "error": result_data.get("error", "Unknown error"),
                                "input": test_input,
                                "expected": expected_output,
                                "actual": None
                            })
                            all_passed = False
                        else:
                            actual_output = result_data.get("result")
                            passed = self._compare_output(actual_output, expected_output)
                            
                            results.append({
                                "test_name": test_name,
                                "passed": passed,
                                "input": test_input,
                                "expected": expected_output,
                                "actual": actual_output,
                                "error": None if passed else "Output mismatch"
                            })
                            if not passed:
                                all_passed = False
                    except json.JSONDecodeError:
                        results.append({
                            "test_name": test_name,
                            "passed": False,
                            "error": f"Invalid output format",
                            "input": test_input,
                            "expected": expected_output,
                            "actual": None
                        })
                        all_passed = False
                else:
                    results.append({
                        "test_name": test_name,
                        "passed": False,
                        "error": "No output produced",
                        "input": test_input,
                        "expected": expected_output,
                        "actual": None
                    })
                    all_passed = False
                    
            except subprocess.TimeoutExpired:
                results.append({
                    "test_name": test_name,
                    "passed": False,
                    "error": f"Code execution timed out after {self.timeout_seconds} seconds",
                    "input": test_input,
                    "expected": expected_output,
                    "actual": None
                })
                all_passed = False
            except Exception as e:
                results.append({
                    "test_name": test_name,
                    "passed": False,
                    "error": f"Execution error: {str(e)}",
                    "input": test_input,
                    "expected": expected_output,
                    "actual": None
                })
                all_passed = False
            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_file)
                except:
                    pass
        
        return {
            "passed": all_passed,
            "test_results": results,
            "total_tests": len(test_cases),
            "passed_tests": sum(1 for r in results if r.get("passed", False))
        }
    
    def _extract_function_name(self, code: str) -> Optional[str]:
        """Extract function name from code."""
        lines = code.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('def '):
                func_name = line.split('def ')[1].split('(')[0].strip()
                return func_name
        return None
    
    def _compare_output(self, actual: Any, expected: Any) -> bool:
        """Compare actual output with expected output."""
        if isinstance(expected, float) and isinstance(actual, (int, float)):
            return abs(float(actual) - float(expected)) < 1e-9
        elif isinstance(expected, list) and isinstance(actual, list):
            if len(expected) != len(actual):
                return False
            return all(self._compare_output(a, e) for a, e in zip(actual, expected))
        else:
            return actual == expected
    
    def _filter_error(self, error: str) -> str:
        """Filter error messages to prevent information leakage."""
        # Remove file paths
        error = re.sub(r'/tmp/[^\s]+', '/tmp/***', error)
        error = re.sub(r'/[^\s]+\.py', '/***.py', error)
        # Remove user home paths
        error = re.sub(r'~/[^\s]+', '~/***', error)
        return error
    
    def _set_limits(self):
        """Set resource limits (Unix only)."""
        try:
            import resource
            # Limit memory (in bytes)
            resource.setrlimit(resource.RLIMIT_AS, (self.max_memory_mb * 1024 * 1024, self.max_memory_mb * 1024 * 1024))
            # Limit CPU time
            resource.setrlimit(resource.RLIMIT_CPU, (self.timeout_seconds, self.timeout_seconds))
        except:
            pass  # Not available on Windows

