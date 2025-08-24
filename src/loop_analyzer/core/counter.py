from loop_analyzer.core.loop import LoopStructure, PatternType
from loop_analyzer.core.pattern_recognizer import PatternRecognizer
from loop_analyzer.patterns.formulas import OptimizedFormulas
from loop_analyzer.core.polyhedron_utils import loop_structure_to_isl_string
from loop_analyzer.wrappers.barvinok_wrapper import count_integer_points

class LatticeCounter:
    def count_hybrid(self, loop_structure: LoopStructure, concrete_params: dict[str, int]) -> int:
        pattern_recognizer = PatternRecognizer()
        pattern = pattern_recognizer.recognize_pattern(loop_structure)
        if pattern == PatternType.LOWER_TRIANGLE:
            return OptimizedFormulas.pattern_1_lower_triangle(concrete_params['n'])
        elif pattern == PatternType.UPPER_TRIANGLE:
            return OptimizedFormulas.pattern_2_upper_triangle(concrete_params['n'])

        return 0

    def count_barvinok(self, loop_structure: LoopStructure, concrete_params: dict[str, int]):
        try:
            substituted_loop = loop_structure.substitute_parameters(concrete_params)

            # перевод в isl представление
            isl_str = loop_structure_to_isl_string(substituted_loop)

            count, time_ms = count_integer_points(isl_str)
            
            return [count, time_ms]
            
        except Exception as e:
            return 0