import subprocess
import time
import re

def count_integer_points(polyhedron_isl_str: str) -> (int,int):
    input_data = f"""S := {polyhedron_isl_str}; card S;"""

    count = 0
    try:
        # запускаем iscc через subprocess
        proc = subprocess.Popen(["iscc"],
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True)
        start = time.perf_counter_ns()
        stdout, stderr = proc.communicate(input=input_data)
        end = time.perf_counter_ns()

        if proc.returncode != 0:
            raise RuntimeError(f"iscc failed: {stderr}")

        match = re.search(r'\{\s*([-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)\s*\}', stdout)
        if match:
            count = int(match.group(1))
        else:
            raise ValueError(f"Cardinal value not found in output: {stdout}")

        pure_time = (end - start) / 1_000_000  # Конвертируем в миллисекунды
        return (count, pure_time)

    except FileNotFoundError:
        raise RuntimeError("iscc not found. Please install barvinok and ensure iscc is in PATH")
