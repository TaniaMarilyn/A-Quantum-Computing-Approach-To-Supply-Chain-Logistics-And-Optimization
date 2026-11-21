import os
import numpy as np
import pandas as pd

from qiskit_optimization import QuadraticProgram
from qiskit_optimization.converters import QuadraticProgramToQubo

# Four-customer routing problem:
# Depot 1, customers 2, 3, 4, 5
nodes = [2, 3, 4, 5]
depot = 1
n = len(nodes)


distance = {
    (1, 1): 0,  (1, 2): 9,  (1, 3): 14, (1, 4): 23, (1, 5): 32,
    (2, 1): 9,  (2, 2): 0,  (2, 3): 21, (2, 4): 22, (2, 5): 36,
    (3, 1): 14, (3, 2): 21, (3, 3): 0,  (3, 4): 25, (3, 5): 38,
    (4, 1): 23, (4, 2): 22, (4, 3): 25, (4, 4): 0,  (4, 5): 42,
    (5, 1): 32, (5, 2): 36, (5, 3): 38, (5, 4): 42, (5, 5): 0,
}

qp = QuadraticProgram("Four_Customer_Routing")

# x_customer_position = 1 if customer is assigned to that position
for customer in nodes:
    for position in range(n):
        qp.binary_var(name=f"x_{customer}_{position}")

linear = {}
quadratic = {}

# Depot to first customer
for customer in nodes:
    linear[f"x_{customer}_0"] = distance[(depot, customer)]

# Last customer back to depot
for customer in nodes:
    name = f"x_{customer}_{n - 1}"
    linear[name] = linear.get(name, 0) + distance[(customer, depot)]

# Distances between consecutive route positions
for position in range(n - 1):
    for customer_a in nodes:
        for customer_b in nodes:
            if customer_a != customer_b:
                var_a = f"x_{customer_a}_{position}"
                var_b = f"x_{customer_b}_{position + 1}"
                quadratic[(var_a, var_b)] = distance[
                    (customer_a, customer_b)
                ]

qp.minimize(linear=linear, quadratic=quadratic)

# Every customer must appear exactly once
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

# Every position must contain exactly one customer
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

print("ORIGINAL FOUR-CUSTOMER ROUTING MODEL")
print(qp.prettyprint())

converter = QuadraticProgramToQubo()
qubo = converter.convert(qp)

print("\nCONVERTED QUBO MODEL")
print(qubo.prettyprint())

print("\nNumber of binary variables:", qubo.get_num_vars())
print("Number of constraints in QUBO:", qubo.get_num_linear_constraints())
print("Expected direct-encoding variables:", n * n)


# ------------------------------------------
# EXPORT ACTUAL QUBO MATRIX
# ------------------------------------------

# Get variable names
variable_names = [var.name for var in qubo.variables]

# Extract the converted QUBO coefficients
linear_coefficients = qubo.objective.linear.to_array()

quadratic_coefficients = (
    qubo.objective.quadratic.to_array(symmetric=True)
)

# Construct the matrix representation
qubo_matrix = quadratic_coefficients.copy()

# Add linear coefficients to the diagonal
qubo_matrix += np.diag(linear_coefficients)

# Create a labelled DataFrame
qubo_df = pd.DataFrame(
    qubo_matrix,
    index=variable_names,
    columns=variable_names
)

# Save inside the project results folder
project_root = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

results_folder = os.path.join(project_root, "results")
os.makedirs(results_folder, exist_ok=True)

output_file = os.path.join(
    results_folder,
    "qubo_matrix.csv"
)

qubo_df.to_csv(output_file)

print("\nQUBO MATRIX EXPORTED SUCCESSFULLY")
print("Matrix dimensions:", qubo_df.shape)
print("Saved location:", output_file)

# Save constant objective separately
print(
    "QUBO constant:",
    qubo.objective.constant
)

