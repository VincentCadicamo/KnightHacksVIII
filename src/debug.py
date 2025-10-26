import numpy as np
import os

def debug_pole_reachability():
    """
    Checks all required photo poles to see if they are reachable
    within the given battery and geofence constraints.
    """

    # --- 1. SET UP PATHS AND PARAMETERS ---
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(script_dir)
        data_dir = os.path.join(root_dir, "data")
    except NameError:
        root_dir = os.getcwd()
        data_dir = os.path.join(root_dir, "data")

    matrix_file = os.path.join(data_dir, "smart_matrix.npy")
    photo_indexes_file = os.path.join(data_dir, "photo_indexes.npy")

    # --- Re-create the exact constraints from your solver ---
    DRONE_BATTERY_FT = 37725

    # This MUST match the value in your build_smart_matrix.py
    FORBIDDEN_PENALTY = 999999999

    # --- 2. LOAD DATA ---
    try:
        matrix = np.load(matrix_file)
        photo_indexes = np.load(photo_indexes_file)
    except Exception as e:
        print(f"Error loading files: {e}")
        return

    print(f"Checking {len(photo_indexes)} photo-poles against 'smart_matrix.npy'...")
    print(f"Battery Limit: {DRONE_BATTERY_FT} ft")
    print(f"Forbidden Cost: {FORBIDDEN_PENALTY}\n")

    unreachable_poles = []
    depot_index = 0 # Assuming depot is 0

    # --- 3. CHECK EVERY POLE ---
    for pole_idx in photo_indexes:
        pole_idx = int(pole_idx) # Ensure it's an integer

        if pole_idx == depot_index:
            print(f"INFO: Pole {pole_idx} is the Depot. Skipping check.")
            continue

        try:
            # Calculate the simplest possible round-trip
            cost_to_pole = matrix[depot_index, pole_idx]
            cost_from_pole = matrix[pole_idx, depot_index]
            round_trip_cost = cost_to_pole + cost_from_pole

            # --- 4. CHECK FOR ERRORS ---

            # Check for geofence (forbidden path) violation
            if round_trip_cost >= FORBIDDEN_PENALTY:
                print(f"🛑 ERROR: Pole {pole_idx} is UNREACHABLE (Forbidden Path).")
                print(f"   Cost to: {cost_to_pole}, Cost from: {cost_from_pole}")
                print(f"   This pole is likely outside the WKT geofence.")
                unreachable_poles.append(pole_idx)

            # Check for battery violation
            elif round_trip_cost > DRONE_BATTERY_FT:
                print(f"⚠️ WARNING: Pole {pole_idx} is UNREACHABLE (Exceeds Battery).")
                print(f"   Round trip: {round_trip_cost} ft > {DRONE_BATTERY_FT} ft")
                unreachable_poles.append(pole_idx)

        except IndexError:
            print(f"🛑 ERROR: Pole {pole_idx} is an INVALID INDEX (out of bounds).")
            unreachable_poles.append(pole_idx)

    # --- 5. SUMMARY ---
    if not unreachable_poles:
        print("\n✅--- All photo-poles appear to be reachable. ---")
        print("This suggests the problem is too complex for the time limit.")
        print("Try increasing 'time_limit.seconds' in VRP-rev1.py to 120 or 300.")
    else:
        print(f"\n❌--- Found {len(unreachable_poles)} unreachable poles. ---")
        print("The solver is failing because these poles are impossible to visit.")
        print("To fix, remove these poles from 'photo_indexes.npy' or fix your geofence/battery.")

if __name__ == "__main__":
    debug_pole_reachability()