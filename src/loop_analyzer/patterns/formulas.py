import math
from typing import Union, Optional
from enum import Enum
import sympy as sp

class OptimizedFormulas:
     @staticmethod
     def pattern_1_lower_triangle(n: Union[int, sp.Symbol]) -> Union[int, sp.Expr]:
         if isinstance(n, int):
             return n * (n - 1) // 2
         else:
             return n * (n - 1) / 2

     @staticmethod
     def pattern_2_upper_triangle(n: Union[int, sp.Symbol]) -> Union[int, sp.Expr]:
         if isinstance(n, int):
             return n * (n + 1) // 2
         else:
             return n * (n + 1) / 2

     @staticmethod
     def pattern_3_trapezoid(n: Union[int, sp.Symbol], k: Union[int, sp.Symbol]) -> Union[int, sp.Expr]:
         return n * (2 * k + 1) - k * (k + 1)

     @staticmethod
     def pattern_4_diagonal(n: Union[int, sp.Symbol]) -> Union[int, sp.Expr]:
         return n * n

     @staticmethod
     def pattern_5_parallelogram(n: Union[int, sp.Symbol], k: Union[int, sp.Symbol]) -> Union[int, sp.Expr]:
         return n * (2 * k + 1) - k * (k + 1)

     @staticmethod
     def pattern_6_band_matrix(n: Union[int, sp.Symbol], b: Union[int, sp.Symbol]) -> Union[int, sp.Expr]:
         return n * (2 * b + 1) - b * (b + 1)
