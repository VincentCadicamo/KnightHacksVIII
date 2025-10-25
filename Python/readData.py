import sys, json, numpy as np

file = sys.argv[1]
arr = np.load(file).tolist()
print(json.dumps(arr))



