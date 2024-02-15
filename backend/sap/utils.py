from typing import Any, List


def chunks(data: List[Any], size: int) -> List[Any]:
    for i in range(0, len(data), size):
        yield data[i: i + size]
