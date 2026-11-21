
from qiskit_optimization import QuadraticProgram
from qiskit_optimization.converters import QuadraticProgramToQubo
from qiskit_algorithms import QAOA
from qiskit_algorithms.optimizers import COBYLA
from qiskit.primitives import Sampler
from qiskit_optimization.algorithms import MinimumEigenOptimizer

import time
import csv
import os

# --------------------------------------------------
# 1. EXPERIMENT SETTINGS
# --------------------------------------------------

DEPOT = 1
NODES = [2, 3, 4, 5]

NUM_TRIALS = 10  # Test with one trial first
QAOA_REPS = 1
MAX_ITERATIONS = 50
EXACT_OPTIMUM = 125

# --------------------------------------------------
# 2. CORRECTED DISTANCE MATRIX
# --------------------------------------------------

DISTANCE = {
    (1, 1): 0,  (1, 2): 9,  (1, 3): 14, (1, 4): 23, (1, 5): 32,
    (2, 1): 9,  (2, 2): 0,  (2, 3): 21, (2, 4): 22, (2, 5): 36,
    (3, 1): 14, (3, 2): 21, (3, 3): 0,  (3, 4): 25, (3, 5): 38,
    (4, 1): 23, (4, 2): 22, (4, 3): 25, (4, 4): 0,  (4, 5): 42,
    (5, 1): 32, (5, 2): 36, (5, 3): 38, (5, 4): 42, (5, 5): 0,
}


# --------------------------------------------------
# 3. BUILD THE QUBO
# --------------------------------------------------

def build_qubo():
    qp = QuadraticProgram("Four_Customer_Routing")

    num_positions = len(NODES)

    # Binary variable: customer at a particular position
    for customer in NODES:
        for position in range(num_positions):
            qp.binary_var(name=f"x_{customer}_{position}")

    linear = {}
    quadratic = {}

    # Depot -> first customer and last customer -> depot
    for customer in NODES:
        linear[f"x_{customer}_0"] = DISTANCE[(DEPOT, customer)]

        linear[f"x_{customer}_{num_positions - 1}"] = (
            DISTANCE[(customer, DEPOT)]
        )

    # Distances between consecutive customer positions
    for position in range(num_positions - 1):
        for a in NODES:
            for b in NODES:
                if a != b:
                    quadratic[
                        (f"x_{a}_{position}", f"x_{b}_{position + 1}")
                    ] = DISTANCE[(a, b)]

    qp.minimize(linear=linear, quadratic=quadratic)

    # Each customer appears exactly once
    for customer in NODES:
        qp.linear_constraint(
            linear={
                f"x_{customer}_{position}": 1
                for position in range(num_positions)
            },
            sense="==",
            rhs=1,
            name=f"customer_{customer}_once",
        )

    # Each position contains exactly one customer
    for position in range(num_positions):
        qp.linear_constraint(
            linear={
                f"x_{customer}_{position}": 1
                for customer in NODES
            },
            sense="==",
            rhs=1,
            name=f"position_{position}_filled",
        )

    # Convert constraints into QUBO penalties
    return QuadraticProgramToQubo().convert(qp)


# --------------------------------------------------
# 4. DECODE AND CHECK THE ROUTE
# --------------------------------------------------

def decode_result(assignment):
    route = [DEPOT]
    num_positions = len(NODES)

    for position in range(num_positions):
        selected = [
            customer
            for customer in NODES
            if assignment.get(f"x_{customer}_{position}", 0) > 0.5
        ]

        if len(selected) != 1:
            return None, None

        route.append(selected[0])

    route.append(DEPOT)

    # Check that every customer occurs exactly once
    if sorted(route[1:-1]) != sorted(NODES):
        return None, None

    # Calculate the original route distance
    route_distance = sum(
        DISTANCE[(route[i], route[i + 1])]
        for i in range(len(route) - 1)
    )

    return route, route_distance


# --------------------------------------------------
# 5. RUN QAOA TRIALS
# --------------------------------------------------

def main():
    qubo = build_qubo()
    records = []

    print("Four-customer routing benchmark")
    print("QUBO variables:", qubo.get_num_vars())
    print("Number of trials:", NUM_TRIALS)
    print("QAOA repetitions (p):", QAOA_REPS)
    print("Maximum optimizer iterations:", MAX_ITERATIONS)
    print("Exact classical optimum:", EXACT_OPTIMUM)

    for trial in range(1, NUM_TRIALS + 1):
        print(f"\nRunning QAOA trial {trial}/{NUM_TRIALS}...")

        qaoa = QAOA(
            sampler=Sampler(),
            optimizer=COBYLA(maxiter=MAX_ITERATIONS),
            reps=QAOA_REPS,
        )

        optimizer = MinimumEigenOptimizer(qaoa)

        start = time.perf_counter()
        result = optimizer.solve(qubo)
        elapsed = time.perf_counter() - start

        assignment = result.variables_dict
        route, route_distance = decode_result(assignment)

        valid = route is not None
        optimal = valid and route_distance == EXACT_OPTIMUM

        print("Route:", route)
        print("Route distance:", route_distance)
        print("QUBO objective value:", result.fval)
        print("Execution time (seconds):", round(elapsed, 4))
        print("Valid route:", valid)
        print("Optimal found:", optimal)

        records.append({
            "Trial": trial,
            "Route": (
                " -> ".join(map(str, route)) if route else ""
            ),
            "Route_distance": (
                route_distance if valid else ""
            ),
            "QUBO_objective": result.fval,
            "Execution_time_seconds": round(elapsed, 6),
            "Valid_route": valid,
            "Optimal_found": optimal,
        })

    # --------------------------------------------------
    # 6. SAVE THE RESULTS
    # --------------------------------------------------

    
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")

os.makedirs(RESULTS_DIR, exist_ok=True)

output_path = os.path.join(RESULTS_DIR, "qaoa_trials.csv")

    with open(output_path, "w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=records[0].keys(),
        )
        writer.writeheader()
        writer.writerows(records)

    # --------------------------------------------------
    # 7. PRINT THE SUMMARY
    # --------------------------------------------------

    valid_records = [
        record for record in records
        if record["Valid_route"]
    ]

    valid_distances = [
        record["Route_distance"]
        for record in valid_records
    ]

    optimal_count = sum(
        record["Optimal_found"] for record in records
    )

    mean_time = sum(
        record["Execution_time_seconds"] for record in records
    ) / len(records)

    print("\n========== QAOA SUMMARY ==========")
    print("Trials completed:", len(records))
    print("Valid routes:", len(valid_records), "/", NUM_TRIALS)
    print("Optimal routes found:", optimal_count, "/", NUM_TRIALS)
    print("Mean execution time (seconds):", round(mean_time, 4))

    if valid_distances:
        print("Best valid route distance:", min(valid_distances))
        print(
            "Mean valid route distance:",
            round(sum(valid_distances) / len(valid_distances), 2),
        )

    print("Results saved to:", output_path)


if __name__ == "__main__":
    main()

