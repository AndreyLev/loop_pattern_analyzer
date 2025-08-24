from typing import Dict
from loop_analyzer.core.loop import PatternType
import math

def get_parameters(n_points: int, pattern: PatternType) -> Dict[str, int]:
    if n_points <= 0:
        raise ValueError("n_points должно быть больше нуля")
    
    C = n_points
    d: Dict[str, int] = {}

    if pattern == PatternType.LOWER_TRIANGLE:
        discriminant = 1 + 8 * C
        if discriminant < 0:
            d['n'] = 1
        else:
            d['n'] = max(1, int((1 + math.sqrt(discriminant)) / 2))
        return d
        
    elif pattern == PatternType.UPPER_TRIANGLE:
        discriminant = 1 + 8 * C
        if discriminant < 0:
            d['n'] = 1
        else:
            d['n'] = max(1, int((-1 + math.sqrt(discriminant)) / 2))
        return d

    d['n'] = max(1, int(math.sqrt(C)))
    return d