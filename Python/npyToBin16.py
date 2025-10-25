import numpy as np
import struct
import os

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) 

NPY_FILE_PATH = os.path.join(root_dir, "data", "distance_matrix.npy")
BIN_FILE_PATH = os.path.join(root_dir, "data", "distance_matrix.bin")

print(f"Loading {NPY_FILE_PATH}...")
matrix = np.load(NPY_FILE_PATH)

matrix = matrix.astype(np.float64)

rows, cols = matrix.shape

print(f"Matrix shape: {rows} rows, {cols} cols")

os.makedirs(os.path.dirname(BIN_FILE_PATH), exist_ok=True)

print(f"Writing to {BIN_FILE_PATH}...")
with open(BIN_FILE_PATH, "wb") as f:
    f.write(struct.pack('i', rows))
    f.write(struct.pack('i', cols))
    f.write(matrix.tobytes())

print("Conversion complete!")