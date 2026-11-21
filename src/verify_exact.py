
from itertools import permutations
import time

nodes = [2, 3, 4]
depot = 1

distance = {
    (1, 1): 0,  (1, 2): 9,  (1, 3): 14, (1, 4): 23,
    (2, 1): 9,  (2, 2): 0,  (2, 3): 21, (2, 4): 22,
    (3, 1): 14, (3, 2): 21, (3, 3): 0,  (3, 4): 25,
    (4, 1): 23, (4, 2): 22, (4, 3): 25, (4, 4): 0,
}

start = time.perf_counter()

best_distance = float("inf")
best_route = None

for order in permutations(nodes):
    route = (depot,) + order + (depot,)
    total = sum(
        distance[(route[i], route[i + 1])]
        for i in range(len(route) - 1)
    )

    if total < best_distance:
        best_distance = total
        best_route = route

elapsed = time.perf_counter() - start

print("EXACT CLASSICAL SOLVER")
print("Best route:", list(best_route))
print("Optimal distance:", best_distance)
print("Routes evaluated:", 6)
print("Execution time (seconds):", round(elapsed, 6))
