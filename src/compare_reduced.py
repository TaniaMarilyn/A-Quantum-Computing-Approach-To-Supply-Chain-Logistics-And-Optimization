
from itertools import permutations
import random
import time
import csv
import os

# Four-customer reduced routing problem
DEPOT = 1
NODES = [2, 3, 4, 5]

DISTANCE = {
    (1, 1): 0,  (1, 2): 9,  (1, 3): 14, (1, 4): 23, (1, 5): 32,
    (2, 1): 9,  (2, 2): 0,  (2, 3): 21, (2, 4): 22, (2, 5): 36,
    (3, 1): 14, (3, 2): 21, (3, 3): 0,  (3, 4): 25, (3, 5): 38,
    (4, 1): 23, (4, 2): 22, (4, 3): 25, (4, 4): 0,  (4, 5): 42,
    (5, 1): 32, (5, 2): 36, (5, 3): 38, (5, 4): 42, (5, 5): 0,
}

def route_distance(order):
    route = [DEPOT] + list(order) + [DEPOT]
    return sum(
        DISTANCE[(route[i], route[i + 1])]
        for i in range(len(route) - 1)
    )


def exact_solver():
    start = time.perf_counter()
    best_order = min(permutations(NODES), key=route_distance)
    elapsed = time.perf_counter() - start
    return list(best_order), route_distance(best_order), elapsed


def simulated_annealing(seed=42, iterations=5000):
    rng = random.Random(seed)

    current = NODES.copy()
    rng.shuffle(current)

    current_cost = route_distance(current)
    best = current.copy()
    best_cost = current_cost

    start = time.perf_counter()

    for step in range(iterations):
        candidate = current.copy()
        i, j = rng.sample(range(len(candidate)), 2)
        candidate[i], candidate[j] = candidate[j], candidate[i]

        candidate_cost = route_distance(candidate)
        temperature = max(0.01, 10 * (1 - step / iterations))
        delta = candidate_cost - current_cost

        if (
            delta < 0
            or rng.random() < pow(2.718281828, -delta / temperature)
        ):
            current = candidate
            current_cost = candidate_cost

        if current_cost < best_cost:
            best = current.copy()
            best_cost = current_cost

    elapsed = time.perf_counter() - start
    return best, best_cost, elapsed


def genetic_algorithm(seed=42, population_size=20, generations=100):
    rng = random.Random(seed)
    all_orders = list(permutations(NODES))

    population = [
        list(rng.choice(all_orders))
        for _ in range(population_size)
    ]

    start = time.perf_counter()

    for _ in range(generations):
        population.sort(key=route_distance)
        next_population = [individual.copy() for individual in population[:4]]

        while len(next_population) < population_size:
            parent = rng.choice(population[:10])
            child = parent.copy()

            i, j = rng.sample(range(len(child)), 2)
            child[i], child[j] = child[j], child[i]

            next_population.append(child)

        population = next_population

    best = min(population, key=route_distance)
    elapsed = time.perf_counter() - start

    return best, route_distance(best), elapsed


def main():
    results = []

    solvers = [
        ("Exact enumeration", exact_solver),
        ("Simulated Annealing", simulated_annealing),
        ("Genetic Algorithm", genetic_algorithm),
    ]

    exact_cost = None

    for name, solver in solvers:
        order, cost, elapsed = solver()
        route = [DEPOT] + list(order) + [DEPOT]
        feasible = sorted(order) == sorted(NODES)

        if name == "Exact enumeration":
            exact_cost = cost

        gap = cost - exact_cost if exact_cost is not None else ""

        print(f"\n{name}")
        print("Route:", route)
        print("Distance:", cost)
        print("Execution time (seconds):", round(elapsed, 6))
        print("Feasible:", feasible)

        results.append({
            "Algorithm": name,
            "Route": " -> ".join(map(str, route)),
            "Distance": cost,
            "Execution_time_seconds": round(elapsed, 8),
            "Feasible": feasible,
            "Gap_from_exact_optimum": gap,
        })

    output_path = os.path.join("results", "four_customer_comparison.csv")
    os.makedirs("results", exist_ok=True)

    with open(output_path, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    print("\nExact optimum:", exact_cost)
    print("Results saved to:", output_path)


if __name__ == "__main__":
    main()
