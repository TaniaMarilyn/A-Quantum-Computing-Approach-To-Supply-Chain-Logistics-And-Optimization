
from itertools import permutations

# Depot and four customers from the same benchmark
nodes = [1, 2, 3, 4, 5]

# Distance matrix from E-n13-k4.vrp
distance = {
    (1, 1): 0,  (1, 2): 9,  (1, 3): 14, (1, 4): 23, (1, 5): 27,
    (2, 1): 9,  (2, 2): 0,  (2, 3): 21, (2, 4): 22, (2, 5): 30,
    (3, 1): 14, (3, 2): 21, (3, 3): 0,  (3, 4): 25, (3, 5): 35,
    (4, 1): 23, (4, 2): 22, (4, 3): 25, (4, 4): 0,  (4, 5): 18,
    (5, 1): 27, (5, 2): 30, (5, 3): 35, (5, 4): 18, (5, 5): 0,
}

best_route = None
best_distance = float("inf")

for order in permutations(nodes[1:]):
    route = (1,) + order + (1,)
    total = sum(
        distance[(route[i], route[i + 1])]
        for i in range(len(route) - 1)
    )

    if total < best_distance:
        best_distance = total
        best_route = route

print("FOUR-CUSTOMER EXACT BASELINE")
print("Best route:", list(best_route))
print("Optimal distance:", best_distance)
print("Routes evaluated:", 24)
