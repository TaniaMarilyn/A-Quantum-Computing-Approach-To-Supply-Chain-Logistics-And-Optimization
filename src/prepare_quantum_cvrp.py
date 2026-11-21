
from pathlib import Path
import re
from itertools import permutations


def load_vrp(filepath):
    text = Path(filepath).read_text(encoding="utf-8")

    def header(key):
        match = re.search(
            rf"^{key}\s*:\s*(.+)$", text, re.MULTILINE
        )
        if not match:
            raise ValueError(f"Missing header: {key}")
        return match.group(1).strip()

    def section(start, end):
        return text.split(start, 1)[1].split(end, 1)[0]

    name = header("NAME")
    n = int(header("DIMENSION"))
    capacity = int(header("CAPACITY"))

    if header("EDGE_WEIGHT_FORMAT") != "LOWER_ROW":
        raise ValueError("Expected LOWER_ROW distance format")

    values = [
        int(x) for x in
        section("EDGE_WEIGHT_SECTION", "DEMAND_SECTION").split()
    ]

    expected = n * (n - 1) // 2
    if len(values) != expected:
        raise ValueError(f"Expected {expected} distances")

    distance = [[0] * n for _ in range(n)]
    k = 0

    for i in range(1, n):
        for j in range(i):
            distance[i][j] = values[k]
            distance[j][i] = values[k]
            k += 1

    demands = {}
    for line in section(
        "DEMAND_SECTION", "DEPOT_SECTION"
    ).splitlines():
        parts = line.split()
        if len(parts) == 2:
            try:
                node, demand = map(int, parts)
                demands[node] = demand
            except ValueError:
                pass

    depot_text = section("DEPOT_SECTION", "EOF")
    depot = int(re.search(r"\d+", depot_text).group())

    return name, distance, demands, capacity, depot


def main():
    filepath = Path("data") / "E-n13-k4.vrp"
    name, distance, demands, capacity, depot = load_vrp(filepath)

    # Start with three customers from the benchmark.
    customers = [2, 3, 4]

    print("Benchmark:", name)
    print("Depot:", depot)
    print("Selected customers:", customers)
    print("Vehicle capacity:", capacity)

    print("\nCustomer demands:")
    for customer in customers:
        print(f"Customer {customer}: {demands[customer]}")

    total_demand = sum(demands[c] for c in customers)
    print("\nTotal selected demand:", total_demand)
    print("Capacity check:", total_demand <= capacity)

    print("\nDistances including depot:")
    nodes = [depot] + customers
    print("Nodes:", nodes)

    for i in nodes:
        row = [distance[i - 1][j - 1] for j in nodes]
        print(f"Node {i}: {row}")

    print("\nAll customer visit orders:")
    best_cost = float("inf")
    best_order = None

    for order in permutations(customers):
        route = [depot] + list(order) + [depot]
        cost = sum(
            distance[route[i] - 1][route[i + 1] - 1]
            for i in range(len(route) - 1)
        )

        print(f"Route {route} | Distance {cost}")

        if cost < best_cost:
            best_cost = cost
            best_order = route

    print("\nBest exact route for this subset:", best_order)
    print("Best exact distance:", best_cost)
    print("\nPreparation complete.")


if __name__ == "__main__":
    main()
