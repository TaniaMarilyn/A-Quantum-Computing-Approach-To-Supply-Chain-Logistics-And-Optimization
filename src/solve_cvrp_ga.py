
from pathlib import Path
import random
import time
import re


def load_vrp(filepath):
    text = Path(filepath).read_text(encoding="utf-8")

    def header(key):
        match = re.search(
            rf"^{key}\s*:\s*(.+)$", text, re.MULTILINE
        )
        if not match:
            raise ValueError(f"Missing header: {key}")
        return match.group(1).strip()

    def get_section(start, end):
        return text.split(start, 1)[1].split(end, 1)[0]

    name = header("NAME")
    n = int(header("DIMENSION"))
    capacity = int(header("CAPACITY"))
    weight_format = header("EDGE_WEIGHT_FORMAT")

    if weight_format != "LOWER_ROW":
        raise ValueError("Expected LOWER_ROW distance format")

    values = [
        int(x) for x in
        get_section("EDGE_WEIGHT_SECTION", "DEMAND_SECTION").split()
    ]

    if len(values) != n * (n - 1) // 2:
        raise ValueError("Incorrect number of distances")

    matrix = [[0] * n for _ in range(n)]
    k = 0

    for i in range(1, n):
        for j in range(i):
            matrix[i][j] = values[k]
            matrix[j][i] = values[k]
            k += 1

    demands = {}
    for line in get_section(
        "DEMAND_SECTION", "DEPOT_SECTION"
    ).splitlines():
        parts = line.split()
        if len(parts) == 2:
            try:
                node, demand = map(int, parts)
                demands[node] = demand
            except ValueError:
                pass

    depot_section = get_section("DEPOT_SECTION", "EOF")
    depot = int(re.search(r"\d+", depot_section).group())

    return name, matrix, demands, capacity, depot


def split_routes(order, demands, capacity, depot):
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


def route_distance(route, matrix):
    return sum(
        matrix[route[i] - 1][route[i + 1] - 1]
        for i in range(len(route) - 1)
    )


def evaluate(order, matrix, demands, capacity, depot):
    routes = split_routes(order, demands, capacity, depot)
    distance = sum(route_distance(r, matrix) for r in routes)
    return distance, routes


def make_child(parent1, parent2):
    """Order crossover: preserves each customer's uniqueness."""
    n = len(parent1)
    left, right = sorted(random.sample(range(n), 2))

    child = [None] * n
    child[left:right + 1] = parent1[left:right + 1]

    remaining = [
        x for x in parent2
        if x not in child
    ]

    positions = [
        i for i in range(n)
        if child[i] is None
    ]

    for position, customer in zip(positions, remaining):
        child[position] = customer

    return child


def solve_ga(matrix, demands, capacity, depot,
             population_size=100, generations=500, seed=42):
    random.seed(seed)
    customers = [c for c in demands if c != depot]

    def fitness(order):
        return evaluate(
            order, matrix, demands, capacity, depot
        )[0]

    population = []
    for _ in range(population_size):
        individual = customers[:]
        random.shuffle(individual)
        population.append(individual)

    best = min(population, key=fitness)[:]
    best_cost = fitness(best)

    start = time.perf_counter()

    for _ in range(generations):
        population.sort(key=fitness)

        if fitness(population[0]) < best_cost:
            best = population[0][:]
            best_cost = fitness(best)

        # Preserve the best few individuals (elitism).
        next_population = [
            individual[:] for individual in population[:5]
        ]

        while len(next_population) < population_size:
            # Tournament selection.
            contestants = random.sample(
                population, min(5, len(population))
            )
            parent1 = min(contestants, key=fitness)

            contestants = random.sample(
                population, min(5, len(population))
            )
            parent2 = min(contestants, key=fitness)

            child = make_child(parent1, parent2)

            # Mutation by swapping two customer positions.
            if random.random() < 0.20:
                i, j = random.sample(range(len(child)), 2)
                child[i], child[j] = child[j], child[i]

            next_population.append(child)

        population = next_population

    candidate = min(population, key=fitness)
    if fitness(candidate) < best_cost:
        best = candidate[:]
        best_cost = fitness(best)

    elapsed = time.perf_counter() - start
    best_cost, routes = evaluate(
        best, matrix, demands, capacity, depot
    )

    return routes, best_cost, elapsed


def validate(routes, demands, capacity, depot):
    customers = [
        node for route in routes for node in route[1:-1]
    ]
    expected = set(demands) - {depot}

    if set(customers) != expected:
        return False
    if len(customers) != len(set(customers)):
        return False

    for route in routes:
        if route[0] != depot or route[-1] != depot:
            return False
        load = sum(demands[c] for c in route[1:-1])
        if load > capacity:
            return False

    return True


if __name__ == "__main__":
    filepath = Path("data") / "E-n13-k4.vrp"

    name, matrix, demands, capacity, depot = load_vrp(filepath)

    routes, cost, elapsed = solve_ga(
        matrix, demands, capacity, depot
    )

    print("Benchmark:", name)
    print("Algorithm: Genetic Algorithm")
    print("Total distance:", cost)
    print("Execution time (seconds):", round(elapsed, 4))
    print("Number of routes:", len(routes))

    for i, route in enumerate(routes, start=1):
        load = sum(demands[c] for c in route[1:-1])
        print(f"Route {i}: {route} | Load: {load}")

    print("Valid solution:", validate(
        routes, demands, capacity, depot
    ))
