
from pathlib import Path
import random
import math
import re
import time

def load_vrp(filepath):
    text = Path(filepath).read_text(encoding="utf-8")

    def section(name, next_name):
        return text.split(name, 1)[1].split(next_name, 1)[0]

    def header_value(key):
        match = re.search(
            rf"^{key}\s*:\s*(.+)$",
            text,
            re.MULTILINE
        )
        if not match:
            raise ValueError(f"Missing header: {key}")
        return match.group(1).strip()

    name = header_value("NAME")
    n = int(header_value("DIMENSION"))
    capacity = int(header_value("CAPACITY"))
    weight_format = header_value("EDGE_WEIGHT_FORMAT")

    if weight_format != "LOWER_ROW":
        raise ValueError(
            f"This script expects LOWER_ROW, got {weight_format}"
        )

    edge_text = section("EDGE_WEIGHT_SECTION", "DEMAND_SECTION")
    distances = [int(x) for x in edge_text.split()]

    expected = n * (n - 1) // 2
    if len(distances) != expected:
        raise ValueError(
            f"Expected {expected} distances, got {len(distances)}"
        )

    matrix = [[0] * n for _ in range(n)]
    k = 0

    for i in range(1, n):
        for j in range(i):
            matrix[i][j] = distances[k]
            matrix[j][i] = distances[k]
            k += 1

    demand_text = section("DEMAND_SECTION", "DEPOT_SECTION")
    demands = {}

    for line in demand_text.splitlines():
        parts = line.split()
        if len(parts) == 2:
            try:
                node, demand = map(int, parts)
                demands[node] = demand
            except ValueError:
                pass

    depot_text = section("DEPOT_SECTION", "EOF")
    depot_match = re.search(r"-?\d+", depot_text)
    if not depot_match:
        raise ValueError("Depot was not found")

    depot = int(depot_match.group())
    if depot == -1:
        raise ValueError("Invalid depot section")

    return name, matrix, demands, capacity, depot


def route_distance(route, matrix):
    total = 0
    for i in range(len(route) - 1):
        total += matrix[route[i] - 1][route[i + 1] - 1]
    return total


def split_into_routes(order, demands, capacity, depot):
    routes = []
    route = [depot]
    load = 0

    for customer in order:
        demand = demands[customer]

        if load + demand > capacity:
            route.append(depot)
            routes.append(route)
            route = [depot]
            load = 0

        route.append(customer)
        load += demand

    route.append(depot)
    routes.append(route)

    return routes


def total_distance(routes, matrix):
    return sum(route_distance(route, matrix) for route in routes)


def is_valid(routes, demands, capacity, depot):
    customers = [
        node
        for route in routes
        for node in route[1:-1]
    ]

    expected = set(demands) - {depot}

    if set(customers) != expected:
        return False

    if len(customers) != len(set(customers)):
        return False

    for route in routes:
        if route[0] != depot or route[-1] != depot:
            return False

        load = sum(demands[node] for node in route[1:-1])
        if load > capacity:
            return False

    return True


def solve_sa(matrix, demands, capacity, depot,
             iterations=20000, seed=42):
    random.seed(seed)
    customers = [node for node in demands if node != depot]

    current = customers[:]
    random.shuffle(current)

    current_routes = split_into_routes(
        current, demands, capacity, depot
    )
    current_cost = total_distance(current_routes, matrix)

    best = current[:]
    best_cost = current_cost

    start_time = time.perf_counter()

    for step in range(iterations):
        candidate = current[:]
        i, j = random.sample(range(len(candidate)), 2)
        candidate[i], candidate[j] = candidate[j], candidate[i]

        candidate_routes = split_into_routes(
            candidate, demands, capacity, depot
        )
        candidate_cost = total_distance(candidate_routes, matrix)

        temperature = max(
            0.01, 100.0 * (1 - step / iterations)
        )

        difference = candidate_cost - current_cost

        if difference < 0 or random.random() < math.exp(
            -difference / temperature
        ):
            current = candidate
            current_cost = candidate_cost

        if current_cost < best_cost:
            best = current[:]
            best_cost = current_cost

    elapsed = time.perf_counter() - start_time

    best_routes = split_into_routes(
        best, demands, capacity, depot
    )

    return best_routes, best_cost, elapsed


if __name__ == "__main__":
    filepath = Path("data") / "E-n13-k4.vrp"

    name, matrix, demands, capacity, depot = load_vrp(filepath)

    routes, cost, elapsed = solve_sa(
        matrix, demands, capacity, depot
    )

    print("Benchmark:", name)
    print("Algorithm: Simulated Annealing")
    print("Total distance:", cost)
    print("Execution time (seconds):", round(elapsed, 4))
    print("Number of routes:", len(routes))

    for i, route in enumerate(routes, start=1):
        load = sum(demands[node] for node in route[1:-1])
        print(f"Route {i}: {route} | Load: {load}")

    print("Valid solution:", is_valid(
        routes, demands, capacity, depot
    ))
