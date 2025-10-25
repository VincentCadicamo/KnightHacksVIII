import numpy as np
import struct
import os

# --- Configuration ---
NPY_FILE_PATH = "data/distance_matrix.npy"
# Save to a new file to avoid confusion
BIN_FILE_PATH = "data/distance_matrix_int16.bin" 
# ---------------------

print(f"Loading {NPY_FILE_PATH}...")
matrix = np.load(NPY_FILE_PATH)

# --- KEY CHANGE ---
# Convert to 2-byte signed integers (max: 32,767)
print("Converting to int16...")
matrix = matrix.astype(np.int16) 

rows, cols = matrix.shape

print(f"Matrix shape: {rows} rows, {cols} cols")
os.makedirs(os.path.dirname(BIN_FILE_PATH), exist_ok=True)

print(f"Writing to {BIN_FILE_PATH}...")
with open(BIN_FILE_PATH, "wb") as f:
    # 1. Write the number of rows as a 4-byte integer
    f.write(struct.pack('i', rows))
    
    # 2. Write the number of columns as a 4-byte integer
    f.write(struct.pack('i', cols))
    
    # 3. Write the entire matrix data as a flat array of 16-bit (2-byte) ints
    f.write(matrix.tobytes())

print("Conversion complete! File is now int16.")

