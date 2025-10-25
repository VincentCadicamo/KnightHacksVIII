import numpy as np
import struct
import os

# --- Configuration ---
NPY_FILE_PATH = "data/distance_matrix.npy"
BIN_FILE_PATH = "data/distance_matrix.bin"
# ---------------------

print(f"Loading {NPY_FILE_PATH}...")
# Load the .npy file
matrix = np.load(NPY_FILE_PATH)

# Ensure it's in a standard format (64-bit float, which is 'double' in Java)
matrix = matrix.astype(np.float64)

rows, cols = matrix.shape

print(f"Matrix shape: {rows} rows, {cols} cols")

# Make sure the 'data' folder exists
os.makedirs(os.path.dirname(BIN_FILE_PATH), exist_ok=True)

print(f"Writing to {BIN_FILE_PATH}...")
with open(BIN_FILE_PATH, "wb") as f:
    # 1. Write the number of rows as a 4-byte integer
    f.write(struct.pack('i', rows))
    
    # 2. Write the number of columns as a 4-byte integer
    f.write(struct.pack('i', cols))
    
    # 3. Write the entire matrix data as a flat array of 64-bit doubles
    f.write(matrix.tobytes())

print("Conversion complete!")
