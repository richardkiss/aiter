from .iter_to_aiter import iter_to_aiter
from .join_aiters import join_aiters
from .map_aiter import map_aiter
from .sharable_aiter import sharable_aiter


def parallel_map_aiter(map_f, worker_count, aiter, q=None, maxsize=1):
    shared_aiter = sharable_aiter(aiter)
    aiters = [map_aiter(map_f, shared_aiter) for _ in range(worker_count)]
    return join_aiters(iter_to_aiter(aiters))
