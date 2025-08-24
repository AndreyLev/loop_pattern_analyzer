#!/usr/bin/env python3

import os
import sys
from pathlib import Path
import clang.cindex
from clang.cindex import CursorKind, TypeKind
from typing import List, Dict, Optional, Union
import sympy as sp

sys.path.append(str(Path(__file__).parent / "src" / "loop_analyzer"))
from .loop import (LoopBound, LoopCondition, LoopStructure, PatternType)

class CppLoopExtractor:
    def __init__(self):
        try:
            self.index = clang.cindex.Index.create()
        except Exception as e:
            print(f"Failed to initialize clang: {e}")
            print("Trying to find compatible libclang...")
            import subprocess
            try:
                result = subprocess.run(['find', '/usr/lib', '-name', 'libclang*.so*'], 
                                      capture_output=True, text=True)
                if result.stdout:
                    libclang_path = result.stdout.strip().split('\n')[0]
                    print(f"Found libclang at: {libclang_path}")
                    clang.cindex.conf.set_library_file(libclang_path)
                    self.index = clang.cindex.Index.create()
                else:
                    raise Exception("No libclang found")
            except Exception as e2:
                print(f"Could not initialize clang: {e2}")
                self.index = None
    
    def parse_file(self, filepath: str) -> clang.cindex.TranslationUnit:
        return self.index.parse(filepath, args=['-std=c++17'])
    
    def extract_expression_text(self, cursor) -> str:
        if not cursor.extent.start.file or not cursor.extent.end.file:
            return ""
        
        try:
            with open(cursor.extent.start.file.name, 'r') as f:
                lines = f.readlines()
                
            start_line = cursor.extent.start.line - 1
            start_col = cursor.extent.start.column - 1
            end_line = cursor.extent.end.line - 1
            end_col = cursor.extent.end.column - 1
            
            if start_line == end_line:
                return lines[start_line][start_col:end_col]
            else:
                result = lines[start_line][start_col:]
                for i in range(start_line + 1, end_line):
                    result += lines[i]
                if end_line < len(lines):
                    result += lines[end_line][:end_col]
                return result
        except:
            return cursor.spelling or ""
    
    def parse_expression_to_sympy(self, expr_text: str) -> Union[sp.Expr, sp.Symbol, int]:
        if not expr_text.strip():
            return sp.Symbol('unknown')

        cleaned_expr = expr_text.strip()

        try:
            return int(cleaned_expr)
        except ValueError:
            pass

        replacements = {
            '&&': '&',
            '||': '|',
            '++': '+1',
            '--': '-1',
            'std::min': 'Min',
            'std::max': 'Max'
        }
        
        for cpp_op, py_op in replacements.items():
            cleaned_expr = cleaned_expr.replace(cpp_op, py_op)

        try:
            import re
            variables = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', cleaned_expr)

            symbols_dict = {}
            for var in variables:
                if var not in ['min', 'max', 'abs', 'int', 'float', 'Min', 'Max']:
                    symbols_dict[var] = sp.Symbol(var)

            if symbols_dict:
                return sp.sympify(cleaned_expr, locals=symbols_dict)
            else:
                return sp.sympify(cleaned_expr)
        except:
            if cleaned_expr.isidentifier():
                return sp.Symbol(cleaned_expr)
            else:
                import re
                match = re.search(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', cleaned_expr)
                if match:
                    return sp.Symbol(match.group())
                return sp.Symbol('unknown')
    
    def parse_loop_bound(self, cursor, var_name: str, parent_scope=None) -> Optional[LoopBound]:
        children = list(cursor.get_children())
        if len(children) < 3:
            return None
            
        init_stmt = children[0] if children[0].kind == CursorKind.DECL_STMT else None
        condition = children[1] if children[1].kind == CursorKind.BINARY_OPERATOR else children[1]
        increment = children[2] if len(children) > 2 else None

        start_value = 0
        if init_stmt:
            for child in init_stmt.get_children():
                if child.kind == CursorKind.VAR_DECL:
                    for subchild in child.get_children():
                        if subchild.kind == CursorKind.INTEGER_LITERAL:
                            start_value = int(self.extract_expression_text(subchild))
                            break
                        elif subchild.kind in [CursorKind.DECL_REF_EXPR, CursorKind.BINARY_OPERATOR, CursorKind.CALL_EXPR, CursorKind.UNEXPOSED_EXPR]:
                            expr_text = self.extract_expression_text(subchild)

                            if expr_text.strip().isidentifier() and parent_scope:
                                resolved_expr = self.find_variable_assignments(parent_scope, expr_text.strip())
                                if resolved_expr:
                                    expr_text = resolved_expr
                            
                            start_value = self.parse_expression_to_sympy(expr_text)
                            break

        end_value = sp.Symbol('n')
        if condition:
            condition_text = self.extract_expression_text(condition)
            operators = ['<=', '>=', '<', '>', '!=', '==']
            for op in operators:
                if op in condition_text:
                    parts = condition_text.split(op)
                    if len(parts) == 2:
                        left_expr = parts[0].strip()
                        right_expr = parts[1].strip()
                        if var_name in left_expr:
                            end_expr = right_expr
                        elif var_name in right_expr:
                            end_expr = left_expr
                        else:
                            continue

                        if end_expr.strip().isidentifier() and parent_scope:
                            resolved_expr = self.find_variable_assignments(parent_scope, end_expr.strip())
                            if resolved_expr:
                                end_expr = resolved_expr
                        
                        end_value = self.parse_expression_to_sympy(end_expr)
                        break

        step_value = 1
        if increment:
            inc_text = self.extract_expression_text(increment)
            if '+=' in inc_text:
                parts = inc_text.split('+=')
                if len(parts) == 2:
                    step_expr = parts[1].strip()
                    step_value = self.parse_expression_to_sympy(step_expr)
            elif '-=' in inc_text:
                parts = inc_text.split('-=')
                if len(parts) == 2:
                    step_expr = parts[1].strip()
                    step_value = -self.parse_expression_to_sympy(step_expr)
            elif '++' in inc_text:
                step_value = 1
            elif '--' in inc_text:
                step_value = -1
        
        return LoopBound(
            start=start_value,
            end=end_value,
            step=step_value,
            variable=var_name
        )
    
    def extract_loop_variable(self, cursor) -> str:
        for child in cursor.get_children():
            if child.kind == CursorKind.DECL_STMT:
                for subchild in child.get_children():
                    if subchild.kind == CursorKind.VAR_DECL:
                        return subchild.spelling
        return ""
    
    def find_conditions_in_loop(self, cursor) -> List[LoopCondition]:
        conditions = []
        
        def visit_node(node):
            if node.kind == CursorKind.IF_STMT:
                children = list(node.get_children())
                if children:
                    condition_expr = self.extract_expression_text(children[0])
                    if condition_expr:
                        variables = self.extract_variables_from_expression(condition_expr)
                        sympy_expr = self.parse_expression_to_sympy(condition_expr)
                        coefficients = self.extract_linear_coefficients(sympy_expr, variables)
                        
                        conditions.append(LoopCondition(
                            expression=condition_expr,
                            variables=variables,
                            is_linear=self.is_sympy_expression_linear(sympy_expr),
                            coefficients=coefficients
                        ))
            
            for child in node.get_children():
                visit_node(child)
        
        visit_node(cursor)
        return conditions
    
    def extract_variables_from_expression(self, expr: str) -> List[str]:
        import re
        variables = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', expr)
        keywords = {'if', 'else', 'for', 'while', 'int', 'float', 'double', 'min', 'max'}
        return [var for var in variables if var not in keywords]
    
    def is_linear_expression(self, expr: str) -> bool:
        import re
        var_pattern = r'[a-zA-Z_][a-zA-Z0-9_]*'
        if re.search(f'{var_pattern}\\s*[*/%]\\s*{var_pattern}', expr):
            return False
        return True
    
    def is_sympy_expression_linear(self, expr: Union[sp.Expr, sp.Symbol, int]) -> bool:
        try:
            if isinstance(expr, (int, float)):
                return True
            if isinstance(expr, sp.Symbol):
                return True
            if isinstance(expr, sp.Expr):
                symbols = expr.free_symbols
                if not symbols:
                    return True

                for symbol in symbols:
                    poly = sp.Poly(expr, symbol)
                    if poly.degree() > 1:
                        return False
                return True
        except:
            return False
        return False
    
    def extract_linear_coefficients(self, expr: Union[sp.Expr, sp.Symbol, int], variables: List[str]) -> Dict[str, int]:
        coefficients = {}
        try:
            if isinstance(expr, (int, float)):
                return {}
            if isinstance(expr, sp.Symbol):
                coefficients[str(expr)] = 1
                return coefficients
            if isinstance(expr, sp.Expr):
                for var_name in variables:
                    var_symbol = sp.Symbol(var_name)
                    if var_symbol in expr.free_symbols:
                        try:
                            coeff = expr.coeff(var_symbol, 1)
                            if coeff is not None:
                                coefficients[var_name] = int(coeff)
                        except:
                            coefficients[var_name] = 1
        except:
            pass
        return coefficients
    
    def validate_and_simplify_bounds(self, loop_structure: LoopStructure) -> LoopStructure:
        simplified_bounds = []
        
        for bound in loop_structure.bounds:
            simplified_bound = LoopBound(
                start=self.simplify_expression(bound.start),
                end=self.simplify_expression(bound.end),
                step=self.simplify_expression(bound.step),
                variable=bound.variable
            )
            simplified_bounds.append(simplified_bound)
        
        return LoopStructure(
            bounds=simplified_bounds,
            conditions=loop_structure.conditions,
            nesting_depth=loop_structure.nesting_depth,
            pattern_type=loop_structure.pattern_type,
            parameters=loop_structure.parameters
        )
    
    def simplify_expression(self, expr: Union[int, str, sp.Symbol, sp.Expr]) -> Union[int, sp.Symbol, sp.Expr]:
        try:
            if isinstance(expr, (int, float)):
                return expr
            if isinstance(expr, str):
                return self.parse_expression_to_sympy(expr)
            if isinstance(expr, (sp.Symbol, sp.Expr)):
                return sp.simplify(expr)
        except:
            if isinstance(expr, str):
                return sp.Symbol(expr)
            return expr
    
    def find_variable_assignments(self, cursor, var_name: str) -> Optional[str]:
        def search_assignments(node):
            if node.kind == CursorKind.DECL_STMT:
                for child in node.get_children():
                    if child.kind == CursorKind.VAR_DECL and child.spelling == var_name:
                        for subchild in child.get_children():
                            if subchild.kind in [CursorKind.CALL_EXPR, CursorKind.BINARY_OPERATOR, CursorKind.UNEXPOSED_EXPR]:
                                return self.extract_expression_text(subchild)

            for child in node.get_children():
                result = search_assignments(child)
                if result:
                    return result
            return None
        
        return search_assignments(cursor)

    def extract_loops_from_cursor(self, cursor, depth=0) -> List[LoopStructure]:
        loops = []
        current_bounds = []
        
        def collect_nested_loops(node, current_depth, bounds_stack, parent_scope=None):
            if node.kind == CursorKind.FOR_STMT:
                var_name = self.extract_loop_variable(node)
                loop_bound = self.parse_loop_bound(node, var_name, parent_scope)
                
                if loop_bound:
                    new_bounds = bounds_stack + [loop_bound]
                    conditions = self.find_conditions_in_loop(node)

                    loop_struct = LoopStructure(
                        bounds=new_bounds,
                        conditions=conditions,
                        nesting_depth=current_depth + 1,
                        pattern_type=None,  # Will be determined later
                        parameters={}
                    )

                    simplified_struct = self.validate_and_simplify_bounds(loop_struct)
                    loops.append(simplified_struct)

                    for child in node.get_children():
                        if child.kind == CursorKind.COMPOUND_STMT:
                            collect_nested_loops(child, current_depth + 1, new_bounds, node)
            else:
                for child in node.get_children():
                    collect_nested_loops(child, current_depth, bounds_stack, parent_scope)
        
        collect_nested_loops(cursor, depth, current_bounds)
        return loops
    
    def extract_loops_from_file(self, filepath: str) -> List[LoopStructure]:
        try:
            tu = self.parse_file(filepath)
            if not tu:
                print(f"Failed to parse {filepath}")
                return []
            
            loops = []
            for cursor in tu.cursor.get_children():
                loops.extend(self.extract_loops_from_cursor(cursor))
            
            return loops
        except Exception as e:
            print(f"Error processing {filepath}: {e}")
            return []
    
    def process_directory(self, data_dir: str) -> Dict[str, List[LoopStructure]]:
        results = {}
        
        for root, dirs, files in os.walk(data_dir):
            for file in files:
                if file.endswith('.cpp'):
                    filepath = os.path.join(root, file)
                    
                    loops = self.extract_loops_from_file(filepath)
                    if loops:
                        results[filepath] = loops
                    else:
                        pass
        
        return results
    
    def print_loop_analysis(self, results: Dict[str, List[LoopStructure]]):
        print("\n" + "="*60)
        print("LOOP EXTRACTION ANALYSIS")
        print("="*60)
        
        for filepath, loops in results.items():
            print(f"\nFile: {filepath}")
            print("-" * 40)
            
            for i, loop in enumerate(loops):
                print(f"\nLoop {i+1}:")
                print(f"  Nesting depth: {loop.nesting_depth}")
                print(f"  Bounds:")
                for j, bound in enumerate(loop.bounds):
                    print(f"    Level {j+1}: {bound.variable} = {bound.start} to {bound.end} step {bound.step}")
                
                if loop.conditions:
                    print(f"  Conditions:")
                    for cond in loop.conditions:
                        print(f"    {cond.expression} (linear: {cond.is_linear})")
                        print(f"    Variables: {cond.variables}")

def main():
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
    else:
        data_dir = "/home/andrei/PycharmProjects/loop_pattern_analyzer/data"

    print(data_dir)
    
    if not os.path.exists(data_dir):
        print(f"Data directory '{data_dir}' not found!")
        return
    
    extractor = CppLoopExtractor()
    results = extractor.process_directory(data_dir)

if __name__ == "__main__":
    main()