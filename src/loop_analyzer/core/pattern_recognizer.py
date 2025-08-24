from typing import Optional

from loop_analyzer.core.loop import PatternType, LoopStructure, LoopBound


class PatternRecognizer:
    """Класс для распознавания паттернов циклов"""
    def __init__(self):
        # Регистрируем методы распознавания для каждого паттерна
        # Порядок важен: от более специфичного к общему
        self.pattern_checkers = [
            (PatternType.LOWER_TRIANGLE, self._check_lower_triangle),
            (PatternType.UPPER_TRIANGLE, self._check_upper_triangle),
        ]

    def recognize_pattern(self, loop_structure: LoopStructure) -> Optional[PatternType]:
        """Определяет тип паттерна для данной структуры циклов"""
        # Проверяем паттерны в порядке от более специфичного к общему
        for pattern_type, checker in self.pattern_checkers:
            if checker(loop_structure):
                loop_structure.pattern_type = pattern_type
                self._extract_parameters(loop_structure, pattern_type)
                return pattern_type
        return None

    def _is_constant_bound(self, bound_expr) -> bool:
        """Проверяет, является ли выражение константой"""
        if isinstance(bound_expr, int):
            return True
        if isinstance(bound_expr, str):
            try:
                int(bound_expr)
                return True
            except ValueError:
                return False

        if hasattr(bound_expr, 'is_number') and bound_expr.is_number:
            return True
        if hasattr(bound_expr, 'is_symbol') and bound_expr.is_symbol:
            return True
        return False

    def _is_variable_reference(self, bound_expr, var_name: str) -> bool:
        """Проверяет, является ли выражение ссылкой на переменную"""
        if isinstance(bound_expr, str):
            return bound_expr.strip() == var_name
        if hasattr(bound_expr, 'name'):
            return bound_expr.name == var_name
        return False

    def _contains_max_min(self, bound_expr) -> bool:
        """Проверяет, содержит ли выражение Max или Min"""
        if hasattr(bound_expr, 'func'):
            return bound_expr.func.__name__ in ['Max', 'Min']
        return False

    def _has_variable_dependency(self, bound_expr, var_name: str) -> bool:
        """Проверяет, зависит ли выражение от данной переменной"""
        if hasattr(bound_expr, 'free_symbols'):
            var_symbols = {sym.name for sym in bound_expr.free_symbols}
            return var_name in var_symbols
        return False

    def _is_diagonal_pattern(self, bound_expr) -> bool:
        """Проверяет паттерн диагональной итерации (сумма размерностей минус 1)"""
        if hasattr(bound_expr, 'args'):
            # Ищем выражения вида n + m - 1
            str_expr = str(bound_expr)
            return '+' in str_expr and '-' in str_expr and '1' in str_expr
        return False

    def _check_lower_triangle(self, loop_structure: LoopStructure) -> bool:
        """Проверяет паттерн 1: нижний треугольник (for i in range(n); for j in range(i))"""
        if loop_structure.nesting_depth != 2:
            return False

        bound1, bound2 = loop_structure.bounds[0], loop_structure.bounds[1]

        # Первый цикл: for i = 0 to n-1
        if not self._is_constant_bound(bound1.start):
            return False

        # Второй цикл: for j = 0 to i-1 (зависит от i)
        if not self._is_constant_bound(bound2.start):
            return False

        # Проверяем, что верхняя граница второго цикла точно равна переменной первого
        return self._is_variable_reference(bound2.end, bound1.variable)

    def _check_upper_triangle(self, loop_structure: LoopStructure) -> bool:
        """Проверяет паттерн 2: верхний треугольник (for i in range(n); for j in range(i, n))"""
        if loop_structure.nesting_depth != 2:
            return False

        bound1, bound2 = loop_structure.bounds[0], loop_structure.bounds[1]

        # Первый цикл: for i = 0 to n-1
        if not self._is_constant_bound(bound1.start):
            return False

        # Второй цикл: for j = i to n-1 (начинается с i)
        if not self._is_variable_reference(bound2.start, bound1.variable):
            return False

        # Верхняя граница должна совпадать с первым циклом
        return str(bound1.end) == str(bound2.end)

    def _extract_parameters(self, loop_structure: LoopStructure, pattern_type: PatternType):
        """Извлекает параметры для формул в зависимости от типа паттерна"""
        if loop_structure.parameters is None:
            loop_structure.parameters = {}

        bounds = loop_structure.bounds

        if pattern_type in [PatternType.LOWER_TRIANGLE, PatternType.UPPER_TRIANGLE]:
            # Параметр: n
            loop_structure.parameters['n'] = bounds[0].end