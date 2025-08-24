from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Union, Dict
import ast
import sympy as sp
from copy import deepcopy

class PatternType(Enum):
    """Перечисление всех 6 паттернов из документа"""
    LOWER_TRIANGLE = 1
    UPPER_TRIANGLE = 2
    TRAPEZOID = 3
    DIAGONAL = 4
    PARALLELOGRAM = 5
    BAND_MATRIX = 6

@dataclass
class LoopBound:
    """Представляет границы одного цикла"""
    start: Union[int, str, sp.Symbol] # начальное значение (может быть символьным)
    end: Union[int, str, sp.Symbol]  # конечное значение
    step: Union[int, str, sp.Symbol]  = 1 # шаг итерации
    variable: str = "" # имя переменной цикла

@dataclass
class LoopCondition:
    """Представляет условие внутри цикла"""
    expression: str # текст условия
    variables: List[str] # переменные, участвующие в условии
    is_linear: bool = False # является ли условие линейным
    coefficients: Dict[str, int] = None # коэффициенты для линейных условий

@dataclass
class LoopStructure:
    """Представляет структуру вложенных циклов"""
    bounds: List[LoopBound] # границы каждого уровня вложеннности
    conditions: List[LoopCondition] = None # условия внутри циклов
    nesting_depth: int = 0 # глубина вложенности
    pattern_type: Optional[PatternType] = None # тип распознанного паттерна
    parameters: Dict[str, Union[int, sp.Symbol]] = None # параметры для формул
    
    def substitute_parameters(self, param_values: Dict[str, Union[int, float]]) -> 'LoopStructure':
        substitutions = {sp.Symbol(k): v for k, v in param_values.items()}

        new_bounds = []
        for bound in self.bounds:
            new_bound = LoopBound(
                start=self._substitute_expr(bound.start, substitutions),
                end=self._substitute_expr(bound.end, substitutions),
                step=self._substitute_expr(bound.step, substitutions),
                variable=bound.variable
            )
            new_bounds.append(new_bound)

        new_conditions = None
        if self.conditions:
            new_conditions = []
            for condition in self.conditions:
                new_condition = LoopCondition(
                    expression=condition.expression,
                    variables=condition.variables,
                    is_linear=condition.is_linear,
                    coefficients=condition.coefficients
                )
                new_conditions.append(new_condition)

        new_parameters = {}
        if self.parameters:
            for k, v in self.parameters.items():
                if isinstance(v, sp.Symbol) and k in param_values:
                    new_parameters[k] = param_values[k]
                elif isinstance(v, sp.Expr):
                    new_parameters[k] = v.subs(substitutions)
                else:
                    new_parameters[k] = v
        
        return LoopStructure(
            bounds=new_bounds,
            conditions=new_conditions,
            nesting_depth=self.nesting_depth,
            pattern_type=self.pattern_type,
            parameters=new_parameters
        )
    
    def _substitute_expr(self, expr, substitutions):
        if isinstance(expr, sp.Expr):
            return expr.subs(substitutions)
        elif isinstance(expr, sp.Symbol):
            return substitutions.get(expr, expr)
        elif isinstance(expr, str):
            try:
                symbol = sp.Symbol(expr)
                if symbol in substitutions:
                    return substitutions[symbol]
            except:
                pass
            return expr
        return expr

