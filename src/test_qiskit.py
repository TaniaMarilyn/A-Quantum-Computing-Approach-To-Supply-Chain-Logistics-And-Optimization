
import qiskit
import qiskit_aer
import qiskit_algorithms
import qiskit_optimization

from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_algorithms import QAOA
from qiskit_algorithms.optimizers import COBYLA

print("Qiskit:", qiskit.__version__)
print("Qiskit Aer:", qiskit_aer.__version__)
print("Qiskit Algorithms:", qiskit_algorithms.__version__)
print("Qiskit Optimization:", qiskit_optimization.__version__)

# Create a two-qubit test circuit
circuit = QuantumCircuit(2, 2)
circuit.h(0)
circuit.cx(0, 1)
circuit.measure([0, 1], [0, 1])

# Run the circuit on the simulator
simulator = AerSimulator()
job = simulator.run(circuit, shots=1000, seed_simulator=42)
result = job.result()
counts = result.get_counts()

print("\nQuantum simulator test: PASSED")
print("Measurement counts:", counts)
print("\nQAOA imports: PASSED")
