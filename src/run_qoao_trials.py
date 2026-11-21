
from qiskit_optimization import QuadraticProgram
from qiskit_optimization.converters import QuadraticProgramToQubo
from qiskit_algorithms import QAOA
from qiskit_algorithms.optimizers import COBYLA
from qiskit.primitives import Sampler
from qiskit_optimization.algorithms import MinimumEigenOptimizer

import time
import csv
import os

NODES = [2, 3, 4]
DEPOT = 1

DISTANCE = {
    (1, 1): 0,  (1, 2): 9,  (1, 3): 14, (1, 4): 23,
    (2, 1): 9,  (2, 2): 0,  (2, 3): 21, (2, 4): 22,
    (3, 1): 14, (3, 2): 21, (3, 3): 0,  (3, 4): 25,
    (4, 1): 23, (4, 2): 22, (4, 3): 25, (4, 4): 0,
}

def build_qubo():
    qp = QuadraticProgram("Reduced_CVRP_Routing")

    for customer in NODES:
        for position in range(3):
            qp.binary_var(name=f"x_{customer}_{position}")

    linear = {}
    quadratic = {}

    for customer in NODES:
        linear[f"x_{customer}_0"] = DISTANCE[(DEPOT, customer)]
        linear[f"x_{customer}_2"] = (
            linear.get(f"x_{customer}_2", 0)
            + DISTANCE[(customer, DEPOT)]
        )

    for position in range(2):
        for a in NODES:
            for b in NODES:
                if a != b:
                    quadratic[(f"x_{a}_{position}",
                               f"x_{b}_{position + 1}")] = DISTANCE[(a, b)]

    qp.minimize(linear=linear, quadratic=quadratic)

    for customer in NODES:
        qp.linear_constraint(
            linear={f"x_{customer}_{p}": 1 for p in range(3)},
            sense="==",
            rhs=1,
            name=f"customer_{customer}_once",
        )

    for position in range(3):
        qp.linear_constraint(
            linear={f"x_{customer}_{position}": 1 for customer in NODES},
            sense="==",
            rhs=1,
            name=f"position_{position}_filled",
        )

    return QuadraticProgramToQubo().convert(qp)

def decode_result(assignment):
    route = [DEPOT]

    for position in range(3):
        selected = [
            customer for customer in NODES
            if assignment.get(f"x_{customer}_{position}", 0) > 0.5
        ]

        if len(selected) != 1:
            return None, None

        route.append(selected[0])

    route.append(DEPOT)

    cost = sum(
        DISTANCE[(route[i], route[i + 1])]
        for i in range(len(route) - 1)
    )

    return route, cost

def main():
    qubo = build_qubo()
    records = []

    for trial in range(1, 11):
        print(f"\nRunning QAOA trial {trial}/10...")

        qaoa = QAOA(
            sampler=Sampler(),
            optimizer=COBYLA(maxiter=50),
            reps=1,
        )

        optimizer = MinimumEigenOptimizer(qaoa)

        start = time.perf_counter()
        result = optimizer.solve(qubo)
        elapsed = time.perf_counter() - start

        assignment = result.variables_dict
        route, route_distance = decode_result(assignment)

        valid = route is not None
        optimal = valid and route_distance == 70

        print("Route:", route)
        print("Route distance:", route_distance)
        print("Execution time (seconds):", round(elapsed, 4))
        print("Valid route:", valid)
        print("Optimal found:", optimal)

        records.append({
            "Trial": trial,
            "Route": " -> ".join(map(str, route)) if route else "",
            "Route_distance": route_distance if valid else "",
            "QUBO_objective": result.fval,
            "Execution_time_seconds": round(elapsed, 6),
            "Valid_route": valid,
            "Optimal_found": optimal,
        })

    os.makedirs("results", exist_ok=True)
    output_path = os.path.join("results", "qaoa_trials.csv")

    with open(output_path, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)

    valid_distances = [
        r["Route_distance"] for r in records
        if r["Valid_route"]
    ]
    optimal_count = sum(r["Optimal_found"] for r in records)
    mean_time = sum(r["Execution_time_seconds"] for r in records) / len(records)

    print("\n========== SUMMARY ==========")
    print("Trials completed:", len(records))
    print("Valid routes:", len(valid_distances))
    print("Optimal routes found:", optimal_count, "/ 10")
    print("Mean execution time (seconds):", round(mean_time, 4))

    if valid_distances:
        print("Best valid route distance:", min(valid_distances))
        print("Mean valid route distance:",
              round(sum(valid_distances) / len(valid_distances), 2))

    print("Results saved to:", output_path)

if __name__ == "__main__":
    main()
