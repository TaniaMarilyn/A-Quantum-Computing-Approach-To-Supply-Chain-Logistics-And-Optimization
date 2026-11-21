

import os
import re

DATA_FILE = os.path.join("data", "E-n13-k4.vrp")
DIMENSION = 13

with open(DATA_FILE, "r") as file:
    lines = file.readlines()

headers = {}
section_start = None

for i, line in enumerate(lines):
    stripped = line.strip()

    if ":" in stripped:
        key, value = stripped.split(":", 1)
        headers[key.strip()] = value.strip()

    if stripped == "EDGE_WEIGHT_SECTION":
        section_start = i + 1
        break

if section_start is None:
    print("ERROR: EDGE_WEIGHT_SECTION not found.")
    raise SystemExit(1)

if headers.get("EDGE_WEIGHT_TYPE") != "EXPLICIT":
    print("ERROR: Expected EXPLICIT edge weights.")
    raise SystemExit(1)

if headers.get("EDGE_WEIGHT_FORMAT") != "LOWER_ROW":
    print("ERROR: Expected LOWER_ROW format.")
    raise SystemExit(1)

values = []

for line in lines[section_start:]:
    stripped = line.strip()

    if stripped in ("DEMAND_SECTION", "DEPOT_SECTION", "EOF"):
        break

    values.extend(int(number) for number in re.findall(r"-?\d+", stripped))

expected = DIMENSION * (DIMENSION - 1) // 2

if len(values) != expected:
    print("ERROR: Incorrect number of distance values.")
    print("Expected:", expected)
    print("Found:", len(values))
    raise SystemExit(1)

matrix = [[0] * DIMENSION for _ in range(DIMENSION)]

index = 0

for i in range(1, DIMENSION):
    for j in range(i):
        matrix[i][j] = values[index]
        matrix[j][i] = values[index]
        index += 1

print("Reconstructed distance matrix successfully.")
print("Nodes are numbered 1 through", DIMENSION)
print("\nDistances from depot 1 to customers 2, 3, 4, 5:")

for customer in [2, 3, 4, 5]:
    print(f"Distance 1 -> {customer}: {matrix[0][customer - 1]}")

print("\nDistances between customers:")
for a in [2, 3, 4, 5]:
    for b in [2, 3, 4, 5]:
        print(f"d({a},{b}) = {matrix[a - 1][b - 1]}", end="   ")
    print()

print("\nFour-customer distance matrix verification complete.")
