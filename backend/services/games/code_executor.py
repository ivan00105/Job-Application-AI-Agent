"""
Code execution service for running user-submitted code safely.
"""
import subprocess
import tempfile
import os
import logging
from typing import Dict, Any, List, Optional
import json

logger = logging.getLogger(__name__)


class CodeExecutor:
    """Service for executing user code in a controlled environment."""
    
    def __init__(self, timeout_seconds: int = 10):
        self.timeout_seconds = timeout_seconds
    
    async def execute_python(
        self,
        code: str,
        test_cases: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Execute Python code against test cases.
        
        Args:
            code: User's Python code
            test_cases: List of test cases with input and expected output
            
        Returns:
            Dictionary with test results
        """
        results = []
        all_passed = True
        
        for i, test_case in enumerate(test_cases):
            test_input = test_case.get("input", {})
            expected_output = test_case.get("expected_output")
            test_name = test_case.get("name", f"Test {i+1}")
            
            # Create a temporary Python file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                # Import json at the top (before user code to ensure it's available)
                f.write("import json\n")
                f.write("\n")
                
                # Write the user's code
                f.write(code)
                f.write("\n\n")
                
                # Add test execution code
                f.write("# Test execution\n")
                f.write("try:\n")
                
                # Extract function name from code (simple heuristic)
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
                    # Named parameters
                    args_str = ", ".join([f"{k}={repr(v)}" for k, v in test_input.items()])
                    call_str = f"{function_name}({args_str})"
                elif isinstance(test_input, (list, tuple)):
                    # Positional arguments
                    args_str = ", ".join([repr(arg) for arg in test_input])
                    call_str = f"{function_name}({args_str})"
                else:
                    # Single argument
                    args_str = repr(test_input)
                    call_str = f"{function_name}({args_str})"
                
                # Execute function and capture result
                # Always capture the return value, unless it's an in-place modification
                if isinstance(test_input, dict):
                    # Set up input variables
                    for key, value in test_input.items():
                        f.write(f"    {key} = {repr(value)}\n")
                    
                    # Check if this is an in-place modification (expected_output is None)
                    # For in-place, we check the modified input variable
                    # Otherwise, we capture the return value
                    if expected_output is None:
                        # In-place modification - check the first input variable after call
                        first_var = list(test_input.keys())[0]
                        f.write(f"    {call_str}\n")
                        f.write(f"    print(json.dumps({{'result': {first_var}, 'status': 'success'}}))\n")
                    else:
                        # Normal function - capture return value
                        f.write(f"    result = {call_str}\n")
                        f.write(f"    print(json.dumps({{'result': result, 'status': 'success'}}))\n")
                else:
                    # Single argument or list - always capture return value
                    f.write(f"    result = {call_str}\n")
                    f.write(f"    print(json.dumps({{'result': result, 'status': 'success'}}))\n")
                f.write("except Exception as e:\n")
                f.write(f"    print(json.dumps({{'error': str(e), 'status': 'error'}}))\n")
                
                temp_file = f.name
            
            try:
                # Execute the code with timeout
                process = subprocess.run(
                    ["python3", temp_file],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                    env={**os.environ, "PYTHONIOENCODING": "utf-8"}
                )
                
                # Parse output
                output = process.stdout.strip()
                error_output = process.stderr.strip()
                
                if error_output:
                    results.append({
                        "test_name": test_name,
                        "passed": False,
                        "error": error_output,
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
                            "error": f"Invalid output format: {output}",
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
        """Extract function name from code (simple heuristic)."""
        lines = code.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('def '):
                # Extract function name
                func_name = line.split('def ')[1].split('(')[0].strip()
                return func_name
        return None
    
    def _compare_output(self, actual: Any, expected: Any) -> bool:
        """Compare actual output with expected output."""
        # Handle different types
        if isinstance(expected, float) and isinstance(actual, (int, float)):
            # Allow small floating point differences
            return abs(float(actual) - float(expected)) < 1e-9
        elif isinstance(expected, list) and isinstance(actual, list):
            # Compare lists (order matters)
            if len(expected) != len(actual):
                return False
            return all(self._compare_output(a, e) for a, e in zip(actual, expected))
        else:
            return actual == expected
    
    async def execute_javascript(
        self,
        code: str,
        test_cases: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Execute JavaScript code against test cases.
        Note: Requires Node.js to be installed.
        """
        results = []
        all_passed = True
        
        for i, test_case in enumerate(test_cases):
            test_input = test_case.get("input", {})
            expected_output = test_case.get("expected_output")
            test_name = test_case.get("name", f"Test {i+1}")
            
            # Create a temporary JavaScript file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                # Write the user's code
                f.write(code)
                f.write("\n\n")
                
                # Add test execution code
                f.write("// Test execution\n")
                f.write("try {\n")
                
                # Extract function name from code
                function_name = self._extract_js_function_name(code)
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
                # For JavaScript, we need to handle different parameter styles
                # Most JS functions in our questions take named parameters as an object
                # or individual parameters
                
                if isinstance(test_input, dict):
                    # Named parameters - check function signature to see if it takes an object
                    # For now, we'll try both: individual params and object
                    # Set up variables first
                    for key, value in test_input.items():
                        f.write(f"    const {key} = {self._js_repr(value)};\n")
                    
                    # Try to determine parameter style from function signature
                    # If function takes one parameter and we have multiple inputs, likely an object
                    # Otherwise, pass individual parameters
                    if len(test_input) == 1:
                        # Single parameter - pass directly
                        first_key = list(test_input.keys())[0]
                        call_str = f"{function_name}({first_key})"
                    else:
                        # Multiple parameters - try individual params first
                        # If that doesn't work, the function might expect an object
                        # We'll pass them as individual params
                        params_str = ", ".join(test_input.keys())
                        call_str = f"{function_name}({params_str})"
                elif isinstance(test_input, (list, tuple)):
                    # Positional arguments
                    args_str = ", ".join([self._js_repr(arg) for arg in test_input])
                    call_str = f"{function_name}({args_str})"
                else:
                    # Single argument
                    arg_var = "testArg"
                    f.write(f"    const {arg_var} = {self._js_repr(test_input)};\n")
                    call_str = f"{function_name}({arg_var})"
                
                # Execute function and capture result
                if isinstance(test_input, dict) and expected_output is None:
                    # In-place modification - check the first input variable after call
                    first_var = list(test_input.keys())[0]
                    f.write(f"    {call_str};\n")
                    f.write(f"    console.log(JSON.stringify({{result: {first_var}, status: 'success'}}));\n")
                else:
                    # Normal function - capture return value
                    f.write(f"    const result = {call_str};\n")
                    f.write(f"    console.log(JSON.stringify({{result: result, status: 'success'}}));\n")
                
                f.write("} catch (e) {\n")
                f.write("    console.log(JSON.stringify({error: e.message, status: 'error'}));\n")
                f.write("}\n")
                
                temp_file = f.name
            
            try:
                # Execute the code with timeout using Node.js
                # Try 'node' first, then 'nodejs' (for some Linux distributions)
                node_cmd = None
                for cmd in ['node', 'nodejs']:
                    try:
                        subprocess.run([cmd, '--version'], capture_output=True, timeout=2, check=True)
                        node_cmd = cmd
                        break
                    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                        continue
                
                if not node_cmd:
                    results.append({
                        "test_name": test_name,
                        "passed": False,
                        "error": "Node.js is not installed or not found in PATH. Please install Node.js to run JavaScript code.",
                        "input": test_input,
                        "expected": expected_output,
                        "actual": None
                    })
                    all_passed = False
                    os.unlink(temp_file)
                    continue
                
                process = subprocess.run(
                    [node_cmd, temp_file],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                    env={**os.environ}
                )
                
                # Parse output
                output = process.stdout.strip()
                error_output = process.stderr.strip()
                
                if error_output:
                    results.append({
                        "test_name": test_name,
                        "passed": False,
                        "error": error_output,
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
                            "error": f"Invalid output format: {output}",
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
    
    def _extract_js_function_name(self, code: str) -> Optional[str]:
        """Extract function name from JavaScript code."""
        lines = code.split('\n')
        for line in lines:
            line = line.strip()
            # Match: function functionName(...) or const functionName = (...) => or functionName = function(...)
            if line.startswith('function '):
                # Extract function name
                func_name = line.split('function ')[1].split('(')[0].strip()
                return func_name
            elif '=' in line and ('=>' in line or 'function' in line):
                # Arrow function or function expression
                # Extract name before =
                func_name = line.split('=')[0].strip()
                # Remove const/let/var if present
                for prefix in ['const', 'let', 'var']:
                    if func_name.startswith(prefix):
                        func_name = func_name[len(prefix):].strip()
                return func_name
        return None
    
    def _js_repr(self, value: Any) -> str:
        """Convert Python value to JavaScript representation."""
        if value is None:
            return "null"
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, str):
            # Escape quotes and newlines
            escaped = value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')
            return f'"{escaped}"'
        elif isinstance(value, (list, tuple)):
            items = ", ".join([self._js_repr(item) for item in value])
            return f"[{items}]"
        elif isinstance(value, dict):
            items = ", ".join([f"{self._js_repr(k)}: {self._js_repr(v)}" for k, v in value.items()])
            return f"{{{items}}}"
        else:
            # Fallback to JSON
            return json.dumps(value)

