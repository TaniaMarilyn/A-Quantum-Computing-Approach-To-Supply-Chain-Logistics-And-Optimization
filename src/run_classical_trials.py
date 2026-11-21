
from itertools import permutations
import random
import time
import csv
import os
import statistics

DEPOT = 1
NODES = [2, 3, 4, 5]
TRIALS = 10

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
    best_order = min(permutations(NODES), key=route_distance)
    return list(best_order), route_distance(best_order)


def simulated_annealing(seed, iterations=5000):
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


def genetic_algorithm(seed, population_size=20, generations=100):
    rng = random.Random(seed)
    all_orders = list(permutations(NODES))

    population = [
        list(rng.choice(all_orders))
        for _ in range(population_size)
    ]

    start = time.perf_counter()

    for _ in range(generations):
        population.sort(key=route_distance)
        next_population = [
            individual.copy() for individual in population[:4]
        ]

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
    exact_order, exact_cost = exact_solver()
    print("Exact optimal distance:", exact_cost)
    print("Exact optimal route:", [DEPOT] + exact_order + [DEPOT])

    results = []

    for algorithm in ("SA", "GA"):
        for trial in range(1, TRIALS + 1):
            seed = 1000 + trial

            if algorithm == "SA":
                order, cost, elapsed = simulated_annealing(seed)
                name = "Simulated Annealing"
            else:
                order, cost, elapsed = genetic_algorithm(seed)
                name = "Genetic Algorithm"

            feasible = sorted(order) == sorted(NODES)
            gap = cost - exact_cost

            row = {
                "Algorithm": name,
                "Trial": trial,
                "Seed": seed,
                "Route": " -> ".join(
                    map(str, [DEPOT] + order + [DEPOT])
                ),
                "Distance": cost,
                "Execution_time_seconds": round(elapsed, 8),
                "Feasible": feasible,
                "Optimality_gap": gap,
                "Optimal": feasible and gap == 0,
            }
            results.append(row)

            print(
                f"{name} | Trial {trial:02d} | "
                f"Distance: {cost} | "
                f"Time: {elapsed:.6f} s | "
                f"Optimal: {row['Optimal']}"
            )

    output_path = os.path.join(
        "results", "classical_trials_4_customers.csv"
    )
    os.makedirs("results", exist_ok=True)

    with open(output_path, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    print("\nSUMMARY")

    for algorithm in ("Simulated Annealing", "Genetic Algorithm"):
        group = [
            row for row in results
            if row["Algorithm"] == algorithm and row["Feasible"]
        ]

        if not group:
            print(f"{algorithm}: no feasible results")
            continue

        distances = [row["Distance"] for row in group]
        times = [row["Execution_time_seconds"] for row in group]
        successes = sum(row["Optimal"] for row in group)

        print(f"\n{algorithm}")
        print("Feasible trials:", len(group), "/", TRIALS)
        print("Optimal trials:", successes, "/", TRIALS)
        print("Best distance:", min(distances))
        print("Mean distance:", round(statistics.mean(distances), 4))
        print("Mean execution time (seconds):", round(statistics.mean(times), 6))

    print("\nDetailed results saved to:", output_path)


if __name__ == "__main__":
    main()
