import time
import random
from statistics import median
import gc
import os
import sys
from pathlib import Path

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = Path(__file__).parent.parent
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))

from loop_analyzer.core.counter import LatticeCounter
from loop_analyzer.core.loop_extractor import CppLoopExtractor
from loop_analyzer.core.pattern_recognizer import PatternRecognizer
from loop_analyzer.utils.parameter_selection import get_parameters

# Очистка памяти перед каждым измерением
def clean_measurement():
    gc.collect()  # Принудительная сборка мусора
    time.sleep(0.001)  # Небольшая пауза

def main():
    data_directory = os.path.join(script_dir, '..', 'data')
    
    try:
        loop_extractor = CppLoopExtractor()
        results = loop_extractor.process_directory(data_directory)
        loops_structure = [results[key][-1] for key in results.keys()]

        if not loops_structure:
            return

        optimized_time_arr = []
        barvinok_time_arr = []
        
        # прогрев
        for i in range(1000):
            start = time.perf_counter_ns()
            end = time.perf_counter_ns()
            t = (end - start) / 1_000_000

        lattice_counter = LatticeCounter()
        pattern_recognizer = PatternRecognizer()
        
        # бенчмарк
        for i in range(1000):
            # случайно генерируем количество точек 2^k
            k = random.randint(20, 50)
            n_points = 2 ** k
            
            for loop_structure in loops_structure:
                clean_measurement()
                start = time.perf_counter_ns()
                pattern = pattern_recognizer.recognize_pattern(loop_structure)
                if pattern is None:
                    continue

                concrete_parameters = get_parameters(n_points, pattern)

                hybrid_count = lattice_counter.count_hybrid(loop_structure, concrete_parameters)
                end = time.perf_counter_ns()

                hybrid_time = (end - start) / 1_000_000

                clean_measurement()

                barvinok_count = lattice_counter.count_barvinok(loop_structure, concrete_parameters)

                barvinok_time = barvinok_count[1]

                optimized_time_arr.append(hybrid_time)
                barvinok_time_arr.append(barvinok_time)

        if optimized_time_arr and barvinok_time_arr:
            optimized_algo_median = median(optimized_time_arr)
            barvinok_algo_median = median(barvinok_time_arr)

            print(f'optimized_algo_time (ms): {round(optimized_algo_median,2)}')
            print(f'barvinok_algo_time (ms): {round(barvinok_algo_median,2)}')
        else:
            print("No valid measurements collected.")
            
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
