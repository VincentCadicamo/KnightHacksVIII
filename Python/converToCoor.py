import numpy as np, re

# Example arrow text
log_line = "0 (Dist:0) -> 1820 (Dist:111) -> 1867 (Dist:114) -> 1822 (Dist:153) -> 1872 (Dist:156)"

# Extract only the integers before "(Dist:...)" 
indices = [int(m.group(1)) for m in re.finditer(r"(\d+)\s*\(Dist:", log_line)]

# Load a single array
points = np.load("data/points_lat_long.npy")

coords = [(points[i][0], points[i][1]) for i in indices]

for lon, lat in coords:
    print(f"Lon= {lon:f}, Lat= {lat:f}")



