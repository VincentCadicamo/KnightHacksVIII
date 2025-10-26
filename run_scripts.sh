#!/bin/sh

set -e

echo "(1/5) [Start running the VRP optimizationalgorithm]"
python ./src/solve_vrp.py

echo "(3/5) [predecessor optimization]"
python ./src/expand_routes.py

echo "(4/5) [Convert VRP tour to formatted output]"
python ./src/converToCoor.py

echo "(5/5) [Running visualization script]"
python ./src/plot_map.py

echo "(All scripts finished!!]"