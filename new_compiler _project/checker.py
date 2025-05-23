import ast
import tempfile
import subprocess
import os
import io
import contextlib
import re
from typing import Dict

symbol_table: Dict[str, str] = {}
SUPPORTED_TYPES = {"int", "float", "str", "bool"}

class TypeErrorException(Exception):
    pass

class TypeChecker(ast.NodeVisitor):
    def __init__(self):
        self.errors = []
        self.warnings = []

    def visit_Assign(self, node):
        if isinstance(node.targets[0], ast.Name):
            var_name = node.targets[0].id
            try:
                value_type = self.infer_type(node.value)
                if var_name in symbol_table:
                    if symbol_table[var_name] != value_type:
                        self.errors.append(
                            f"Type Error: Variable '{var_name}' was '{symbol_table[var_name]}', now '{value_type}' at line {node.lineno}"
                        )
                else:
                    symbol_table[var_name] = value_type
            except TypeErrorException as e:
                self.errors.append(str(e))
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        for stmt in node.body:
            self.visit(stmt)

    def visit_For(self, node):
        self.visit(node.iter)
        for stmt in node.body:
            self.visit(stmt)

    def visit_If(self, node):
        self.visit(node.test)
        for stmt in node.body:
            self.visit(stmt)
        for stmt in node.orelse:
            self.visit(stmt)

    def visit_BinOp(self, node):
        left_type = self.infer_type(node.left)
        right_type = self.infer_type(node.right)
        if left_type != right_type:
            raise TypeErrorException(f"Type Mismatch at line {node.lineno}")
        return left_type

    def visit_Call(self, node):
        # Check for regex calls like re.match, re.search, etc.
        if isinstance(node.func, ast.Attribute):
            if (isinstance(node.func.value, ast.Name) and
                node.func.value.id == 're' and
                node.func.attr in {'match', 'search', 'fullmatch', 'findall', 'finditer'}):

                # We expect at least 2 arguments: pattern and string
                if len(node.args) >= 2:
                    pattern_type = self.infer_type(node.args[0])
                    string_type = self.infer_type(node.args[1])
                    if pattern_type != 'str':
                        self.errors.append(f"Type Error: regex pattern argument must be 'str' at line {node.lineno}")
                    if string_type != 'str':
                        self.errors.append(f"Type Error: regex match argument must be 'str' at line {node.lineno}")
                else:
                    self.errors.append(f"Type Error: regex function '{node.func.attr}' expects at least 2 arguments at line {node.lineno}")

        self.generic_visit(node)

    def infer_type(self, node):
        if isinstance(node, ast.Constant):
            py_type = type(node.value).__name__
            if py_type in SUPPORTED_TYPES:
                return py_type
            return "unknown"
        elif isinstance(node, ast.Name):
            if node.id in symbol_table:
                return symbol_table[node.id]
            raise TypeErrorException(f"Undefined variable '{node.id}' at line {node.lineno}")
        elif isinstance(node, ast.BinOp):
            return self.visit_BinOp(node)
        elif isinstance(node, ast.Call):
            # If call is like str(), int(), float(), bool() - infer type as function name
            if isinstance(node.func, ast.Name) and node.func.id in SUPPORTED_TYPES:
                return node.func.id
            return "unknown"
        return "unknown"

def run_python_checker(code):
    global symbol_table
    symbol_table = {}
    try:
        tree = ast.parse(code)
        checker = TypeChecker()
        checker.visit(tree)
        if checker.errors:
            return "\n".join(checker.errors)
        result = "No type errors found."
        if checker.warnings:
            result += "\n\nWarnings:\n" + "\n".join(checker.warnings)
        return result
    except SyntaxError as e:
        return f"Syntax Error: {e}"

def execute_code(code, language):
    try:
        if language == "Python":
            with io.StringIO() as buf, contextlib.redirect_stdout(buf):
                exec_globals = {"re": re}  # Allow regex usage in executed code
                exec(code, exec_globals)
                return buf.getvalue()

        # Support for other languages (C, C++, Java) as before...

    except subprocess.CalledProcessError as e:
        return f"Compilation/Execution Error: {e}"
    except Exception as e:
        return f"Runtime Error: {e}"
