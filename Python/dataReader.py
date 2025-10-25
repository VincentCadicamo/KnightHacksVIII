import numpy as np
arr = np.load("points_lat_long.npy")  # shape (N,2), columns: lon, lat
np.savetxt("points_lat_long.csv", arr, delimiter=",", fmt="%.10f")