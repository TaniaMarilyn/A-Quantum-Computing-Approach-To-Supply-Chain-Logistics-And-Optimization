
from pathlib import Path

def inspect_benchmark(filepath):
    text = Path(filepath).read_text(encoding="utf-8")

    metadata = {}
    for line in text.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            metadata[key.strip()] = value.strip()

    n = int(metadata["DIMENSION"])
    capacity = int(metadata["CAPACITY"])
    name = metadata["NAME"]

    edge_section = text.split("EDGE_WEIGHT_SECTION", 1)[1]
    edge_section = edge_section.split("DEMAND_SECTION", 1)[0]
    distances = [int(x) for x in edge_section.split()]

    expected = n * (n - 1) // 2
    if len(distances) != expected:
        raise ValueError(
            f"Expected {expected} distances, found {len(distances)}"
        )

    # Reconstruct the symmetric matrix from LOWER_ROW data.
    matrix = [[0] * n for _ in range(n)]
    k = 0

    for i in range(1, n):
        for j in range(i):
            matrix[i][j] = distances[k]
            matrix[j][i] = distances[k]
            k += 1

    demand_section = text.split("DEMAND_SECTION", 1)[1]
    demand_section = demand_section.split("DEPOT_SECTION", 1)[0]

    demands = {}
    for line in demand_section.splitlines():
        parts = line.split()
        if len(parts) == 2:
            node, demand = map(int, parts)
            demands[node] = demand

    depot_section = text.split("DEPOT_SECTION", 1)[1]
    depot = int(depot_section.split()[0])

    print("Benchmark:", name)
    print("Total nodes:", n)
    print("Customers:", n - 1)
    print("Depot node:", depot)
    print("Vehicle capacity:", capacity)
    print("Distances loaded:", len(distances))
    print("Customer demands:", demands)
    print("\nDistance matrix:")
    for row in matrix:
        print(row)

    print("\nData validation:")
    print("Matrix is symmetric:",
          all(matrix[i][j] == matrix[j][i]
              for i in range(n) for j in range(n)))
    print("Diagonal is zero:",
          all(matrix[i][i] == 0 for i in range(n)))
    print("All demands loaded:", len(demands) == n)

if __name__ == "__main__":
    inspect_benchmark("data/E-n13-k4.vrp")
