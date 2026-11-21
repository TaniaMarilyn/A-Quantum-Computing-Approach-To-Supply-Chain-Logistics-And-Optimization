
from qiskit_optimization import QuadraticProgram
from qiskit_optimization.converters import QuadraticProgramToQubo
from qiskit_algorithms import QAOA
from qiskit_algorithms.optimizers import COBYLA
from qiskit.primitives import Sampler
from qiskit_optimization.algorithms import MinimumEigenOptimizer
from itertools import permutations
import time

# Four-customer routing problem
depot = 1
nodes = [2, 3, 4, 5]
n = len(nodes)

# Distance matrix
distance = {
    (1, 1): 0,  (1, 2): 9,  (1, 3): 14, (1, 4): 23, (1, 5): 32,
    (2, 1): 9,  (2, 2): 0,  (2, 3): 21, (2, 4): 22, (2, 5): 36,
    (3, 1): 14, (3, 2): 21, (3, 3): 0,  (3, 4): 25, (3, 5): 38,
    (4, 1): 23, (4, 2): 22, (4, 3): 25, (4, 4): 0,  (4, 5): 42,
    (5, 1): 32, (5, 2): 36, (5, 3): 38, (5, 4): 42, (5, 5): 0,
}
# Build the quadratic optimization problem
qp = QuadraticProgram("Four_Customer_Routing")

for customer in nodes:
    for position in range(n):
        qp.binary_var(name=f"x_{customer}_{position}")

linear = {}
quadratic = {}

# Travel from depot to first customer
for customer in nodes:
    linear[f"x_{customer}_0"] = distance[(depot, customer)]

# Travel from last customer back to depot
for customer in nodes:
    linear[f"x_{customer}_{n - 1}"] = distance[(customer, depot)]

# Travel between consecutive customers
for position in range(n - 1):
    for a in nodes:
        for b in nodes:
            if a != b:
                var_a = f"x_{a}_{position}"
                var_b = f"x_{b}_{position + 1}"
                quadratic[(var_a, var_b)] = distance[(a, b)]

qp.minimize(linear=linear, quadratic=quadratic)

# Every customer appears exactly once
for customer in nodes:
    qp.linear_constraint(
        linear={
            f"x_{customer}_{position}": 1
            for position in range(n)
        },
        sense="==",
        rhs=1,
        name=f"customer_{customer}_once",
    )

# Every position contains exactly one customer
for position in range(n):
    qp.linear_constraint(
        linear={
            f"x_{customer}_{position}": 1
            for customer in nodes
        },
        sense="==",
        rhs=1,
        name=f"position_{position}_filled",
    )

# Convert constrained model to QUBO
qubo = QuadraticProgramToQubo().convert(qp)

print("Number of QUBO variables:", qubo.get_num_vars())
print("Starting QAOA on the simulator...")
print("QAOA repetitions (p): 1")
print("Classical optimizer iterations: 50")

qaoa = QAOA(
    sampler=Sampler(),
    optimizer=COBYLA(maxiter=50),
    reps=1,
)

optimizer = MinimumEigenOptimizer(qaoa)

start = time.perf_counter()
result = optimizer.solve(qubo)
elapsed = time.perf_counter() - start

print("\nQAOA RESULT")
print("QUBO objective value:", result.fval)
print("Execution time (seconds):", round(elapsed, 4))

# Decode the returned assignment and verify feasibility
assignment = result.variables_dict
route = []
feasible = True

for position in range(n):
    selected = [
        customer
        for customer in nodes
        if assignment.get(f"x_{customer}_{position}", 0) > 0.5
    ]

    if len(selected) != 1:
        feasible = False
        break

    route.append(selected[0])

if len(route) != n or len(set(route)) != n:
    feasible = False

if feasible:
    full_route = [depot] + route + [depot]

    route_distance = sum(
        distance[(full_route[i], full_route[i + 1])]
        for i in range(len(full_route) - 1)
    )

    # Exact classical benchmark
    exact_best = float("inf")
    exact_route = None

    for order in permutations(nodes):
        candidate = [depot] + list(order) + [depot]
        cost = sum(
            distance[(candidate[i], candidate[i + 1])]
            for i in range(len(candidate) - 1)
        )

        if cost < exact_best:
            exact_best = cost
            exact_route = candidate

    print("Decoded route:", full_route)
    print("Decoded route distance:", route_distance)
    print("Exact classical route:", exact_route)
    print("Exact classical optimum:", exact_best)
    print("Optimality gap:", route_distance - exact_best)
    print("Matches exact optimum:", route_distance == exact_best)
    print("Feasible assignment: True")
else:
    print("Feasible assignment: False")
    print("The returned assignment does not define a complete valid route.")


