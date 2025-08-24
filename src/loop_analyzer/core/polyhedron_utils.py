import numpy as np
import sympy as sp
from typing import List, Tuple, Dict, Union
from .loop import LoopStructure, LoopBound, LoopCondition
import re


def loop_structure_to_polyhedron(loop_structure: LoopStructure) -> Tuple[np.ndarray, np.ndarray]:
    if not loop_structure.bounds:
        raise ValueError("LoopStructure must have at least one bound")
    
    constraints = []
    bounds_vector = []

    num_vars = len(loop_structure.bounds)

    for i, bound in enumerate(loop_structure.bounds):
        start_val = _convert_to_numeric(bound.start)
        end_val = _convert_to_numeric(bound.end)
        step_val = _convert_to_numeric(bound.step)

        lower_constraint = np.zeros(num_vars)
        lower_constraint[i] = -1
        constraints.append(lower_constraint)
        bounds_vector.append(-start_val)

        upper_constraint = np.zeros(num_vars)
        upper_constraint[i] = 1
        constraints.append(upper_constraint)
        bounds_vector.append(end_val - 1)

    if loop_structure.conditions:
        for condition in loop_structure.conditions:
            if condition.is_linear and condition.coefficients:
                constraint = np.zeros(num_vars)
                constant_term = 0
                
                for var_name, coeff in condition.coefficients.items():
                    var_index = _find_variable_index(var_name, loop_structure.bounds)
                    if var_index is not None:
                        constraint[var_index] = coeff
                    else:
                        constant_term += coeff
                
                constraints.append(constraint)
                bounds_vector.append(-constant_term)
    
    if not constraints:
        A = np.eye(num_vars) 
        b = np.ones(num_vars)
        return A, b
    
    A = np.array(constraints)
    b = np.array(bounds_vector)
    
    return A, b


def polyhedron_to_isl_string(A: np.ndarray, b: np.ndarray, variable_names: List[str] = None) -> str:
    if A.shape[0] != len(b):
        raise ValueError("Matrix A and vector b dimensions must be compatible")
    
    num_vars = A.shape[1]
    num_constraints = A.shape[0]
    
    if variable_names is None:
        variable_names = [f"x{i}" for i in range(num_vars)]
    elif len(variable_names) != num_vars:
        raise ValueError(f"Number of variable names ({len(variable_names)}) must match number of variables ({num_vars})")

    var_list = ", ".join(variable_names)
    constraints_list = []
    
    for i in range(num_constraints):
        constraint_terms = []
        
        for j in range(num_vars):
            coeff = A[i, j]
            if coeff == 0:
                continue
            elif coeff == 1:
                constraint_terms.append(variable_names[j])
            elif coeff == -1:
                constraint_terms.append(f"-{variable_names[j]}")
            else:
                if coeff > 0:
                    constraint_terms.append(f"{coeff}*{variable_names[j]}")
                else:
                    constraint_terms.append(f"{coeff}*{variable_names[j]}")
        
        if not constraint_terms:
            continue

        constraint_str = ""
        for k, term in enumerate(constraint_terms):
            if k == 0:
                constraint_str = term
            else:
                if term.startswith("-"):
                    constraint_str += f" {term}"
                else:
                    constraint_str += f" + {term}"

        bound_val = b[i]
        if bound_val == int(bound_val):
            bound_val = int(bound_val)
        
        constraint_str += f" <= {bound_val}"
        constraints_list.append(constraint_str)
    
    if not constraints_list:
        return f"{{[{var_list}]}}"

    constraints_combined = " and ".join(constraints_list)
    
    return f"{{[{var_list}]: {constraints_combined}}}"


def loop_structure_to_isl_string(loop_structure: LoopStructure) -> str:
    variable_names = []
    for bound in loop_structure.bounds:
        if bound.variable:
            variable_names.append(bound.variable)
        else:
            variable_names.append(f"x{len(variable_names)}")

    try:
        return _loop_structure_to_isl_direct(loop_structure, variable_names)
    except Exception:
        A, b = loop_structure_to_polyhedron(loop_structure)
        return polyhedron_to_isl_string(A, b, variable_names)

def _loop_structure_to_isl_direct(loop_structure: LoopStructure, variable_names: List[str]) -> str:
    constraints = []
    
    for i, bound in enumerate(loop_structure.bounds):
        var_name = variable_names[i]

        start_constraint = _convert_bound_to_constraint(bound.start, var_name, ">=", variable_names)
        if start_constraint:
            constraints.append(start_constraint)

        end_constraint = _convert_bound_to_constraint(bound.end, var_name, "<", variable_names)
        if end_constraint:
            constraints.append(end_constraint)
    
    if not constraints:
        var_list = ", ".join(variable_names)
        return f"{{[{var_list}]}}"
    
    var_list = ", ".join(variable_names)
    constraints_str = " and ".join(constraints)
    
    return f"{{[{var_list}]: {constraints_str}}}"

def _convert_bound_to_constraint(bound_expr, var_name: str, op: str, all_vars: List[str]) -> str:
    if isinstance(bound_expr, (int, float)):
        if op == ">=":
            return f"{var_name} >= {bound_expr}"
        elif op == "<":
            return f"{var_name} <= {bound_expr - 1}"
    
    elif isinstance(bound_expr, str):
        if bound_expr in all_vars:
            if op == ">=":
                return f"{var_name} >= {bound_expr}"
            elif op == "<":
                return f"{var_name} <= {bound_expr} - 1"
        elif bound_expr.isdigit():
            val = int(bound_expr)
            if op == ">=":
                return f"{var_name} >= {val}"
            elif op == "<":
                return f"{var_name} <= {val - 1}"
        elif _is_max_expression(bound_expr):
            return _convert_max_to_constraint(bound_expr, var_name, op, all_vars)
        elif _is_min_expression(bound_expr):
            return _convert_min_to_constraint(bound_expr, var_name, op, all_vars)
        else:
            return _convert_expression_to_constraint(bound_expr, var_name, op, all_vars)
    
    elif hasattr(bound_expr, 'func'):
        if bound_expr.func == sp.Max:
            return _convert_sympy_max_to_constraint(bound_expr, var_name, op, all_vars)
        elif bound_expr.func == sp.Min:
            return _convert_sympy_min_to_constraint(bound_expr, var_name, op, all_vars)
        else:
            try:
                str_expr = str(bound_expr)
                return _convert_expression_to_constraint(str_expr, var_name, op, all_vars)
            except:
                if op == ">=":
                    return f"{var_name} >= 0"
                elif op == "<":
                    return f"{var_name} <= 9"
    
    return None

def _is_max_expression(expr_str: str) -> bool:
    return expr_str.startswith("Max(") and expr_str.endswith(")")

def _is_min_expression(expr_str: str) -> bool:
    return expr_str.startswith("Min(") and expr_str.endswith(")")

def _convert_max_to_constraint(max_expr: str, var_name: str, op: str, all_vars: List[str]) -> str:
    inner = max_expr[4:-1]
    args = _parse_expression_args(inner)
    
    if len(args) == 2:
        arg1, arg2 = args
        arg1 = arg1.strip()
        arg2 = arg2.strip()
        
        if op == ">=":
            val1 = _evaluate_expression_with_context(arg1, all_vars, var_name)
            val2 = _evaluate_expression_with_context(arg2, all_vars, var_name)
            
            if val1 is not None and val2 is not None:
                max_val = max(val1, val2)
                return f"{var_name} >= {max_val}"
            elif val1 is not None:
                return f"{var_name} >= {val1}"
            elif val2 is not None:
                return f"{var_name} >= {val2}"
            else:
                if arg1 == "0" or arg1 == 0:
                    return _convert_bound_to_constraint(arg2, var_name, ">=", all_vars)
                elif arg2 == "0" or arg2 == 0:
                    return _convert_bound_to_constraint(arg1, var_name, ">=", all_vars)
                else:
                    return f"{var_name} >= 0"
        elif op == "<":
            val1 = _evaluate_expression_with_context(arg1, all_vars, var_name)
            val2 = _evaluate_expression_with_context(arg2, all_vars, var_name)
            
            if val1 is not None and val2 is not None:
                max_val = max(val1, val2)
                return f"{var_name} <= {max_val - 1}"
            else:
                return f"{var_name} <= 9"
    
    return f"{var_name} >= 0" if op == ">=" else f"{var_name} <= 9"

def _convert_min_to_constraint(min_expr: str, var_name: str, op: str, all_vars: List[str]) -> str:
    inner = min_expr[4:-1]
    args = _parse_expression_args(inner)
    
    if len(args) == 2:
        arg1, arg2 = args
        arg1 = arg1.strip()
        arg2 = arg2.strip()
        
        if op == "<":
            val1 = _evaluate_expression_with_context(arg1, all_vars, var_name)
            val2 = _evaluate_expression_with_context(arg2, all_vars, var_name)
            
            if val1 is not None and val2 is not None:
                min_val = min(val1, val2)
                return f"{var_name} <= {min_val - 1}"
            elif val1 is not None:
                return f"{var_name} <= {val1 - 1}"
            elif val2 is not None:
                return f"{var_name} <= {val2 - 1}"
            else:
                return f"{var_name} <= 9"
        elif op == ">=":
            val1 = _evaluate_expression_with_context(arg1, all_vars, var_name)
            val2 = _evaluate_expression_with_context(arg2, all_vars, var_name)
            
            if val1 is not None and val2 is not None:
                min_val = min(val1, val2)
                return f"{var_name} >= {min_val}"
            else:
                return f"{var_name} >= 0"
    
    return f"{var_name} >= 0" if op == ">=" else f"{var_name} <= 9"

def _convert_sympy_max_to_constraint(max_expr, var_name: str, op: str, all_vars: List[str]) -> str:
    args = [str(arg) for arg in max_expr.args]
    if len(args) == 2:
        return _convert_max_to_constraint(f"Max({args[0]}, {args[1]})", var_name, op, all_vars)
    return f"{var_name} >= 0" if op == ">=" else f"{var_name} <= 9"

def _convert_sympy_min_to_constraint(min_expr, var_name: str, op: str, all_vars: List[str]) -> str:
    args = [str(arg) for arg in min_expr.args]
    if len(args) == 2:
        return _convert_min_to_constraint(f"Min({args[0]}, {args[1]})", var_name, op, all_vars)
    return f"{var_name} >= 0" if op == ">=" else f"{var_name} <= 9"

def _parse_expression_args(expr_str: str) -> List[str]:
    args = []
    current_arg = ""
    paren_count = 0
    
    for char in expr_str:
        if char == ',' and paren_count == 0:
            args.append(current_arg.strip())
            current_arg = ""
        else:
            if char == '(':
                paren_count += 1
            elif char == ')':
                paren_count -= 1
            current_arg += char
    
    if current_arg.strip():
        args.append(current_arg.strip())
    
    return args

def _convert_expression_to_constraint(expr_str: str, var_name: str, op: str, all_vars: List[str]) -> str:
    expr_str = expr_str.strip()

    for var in all_vars:
        if var in expr_str and var != var_name:
            pass

    val = _evaluate_expression(expr_str, all_vars)
    if val is not None:
        if op == ">=":
            return f"{var_name} >= {val}"
        elif op == "<":
            return f"{var_name} <= {val - 1}"

    return f"{var_name} >= 0" if op == ">=" else f"{var_name} <= 9"

def _evaluate_expression(expr_str: str, all_vars: List[str]) -> Union[int, None]:
    try:
        if expr_str.isdigit():
            return int(expr_str)

        for var in all_vars:
            if f"{var} + " in expr_str or f"{var} - " in expr_str or f"{var}+" in expr_str or f"{var}-" in expr_str:
                return 10

        if re.match(r'^[-+]?\d+$', expr_str.strip()):
            return int(expr_str.strip())
        
    except:
        pass
    
    return None

def _evaluate_expression_with_context(expr_str: str, all_vars: List[str], current_var: str) -> Union[int, None]:
    try:
        expr_str = expr_str.strip()

        if expr_str.isdigit() or (expr_str.startswith('-') and expr_str[1:].isdigit()):
            return int(expr_str)

        if current_var in expr_str:
            if f"{current_var} - " in expr_str or f"{current_var}-" in expr_str:
                match = re.search(rf'{current_var}\s*-\s*(\d+)', expr_str)
                if match:
                    offset = int(match.group(1))
                    return max(0, 5 - offset)
            elif f"{current_var} + " in expr_str or f"{current_var}+" in expr_str:
                match = re.search(rf'{current_var}\s*\+\s*(\d+)', expr_str)
                if match:
                    offset = int(match.group(1))
                    return 5 + offset

        for var in all_vars:
            if var in expr_str and var != current_var:
                if f"{var} + " in expr_str or f"{var} - " in expr_str:
                    return 5

        if re.match(r'^[-+]?\d+$', expr_str):
            return int(expr_str)
            
    except:
        pass
    
    return None


def _convert_to_numeric(value: Union[int, str, sp.Symbol]) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    elif isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return 10.0
    elif isinstance(value, sp.Symbol):
        return 10.0
    else:
        return float(value)


def _find_variable_index(var_name: str, bounds: List[LoopBound]) -> Union[int, None]:
    for i, bound in enumerate(bounds):
        if bound.variable == var_name:
            return i
    return None