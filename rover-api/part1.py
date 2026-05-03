import threading
import requests
import time
import copy

# =========================
# MAP READING
# =========================

def read_map(filename):
    with open(filename, "r") as f:
        first_line = f.readline().strip().split()
        rows, cols = int(first_line[0]), int(first_line[1])
        land = []
        for _ in range(rows):
            land.append(f.readline().strip().split())
    return rows, cols, land


ROWS, COLS, BASE_MAP = read_map("map1.txt")

# =========================
# DIRECTION HANDLING
# =========================

DIRECTIONS = ["N", "E", "S", "W"]

MOVE = {
    "N": (-1, 0),
    "E": (0, 1),
    "S": (1, 0),
    "W": (0, -1)
}

def turn_left(d):
    return DIRECTIONS[(DIRECTIONS.index(d) - 1) % 4]

def turn_right(d):
    return DIRECTIONS[(DIRECTIONS.index(d) + 1) % 4]

# =========================
# ROVER EXECUTION LOGIC
# =========================

def run_rover(rover_id):
    land = copy.deepcopy(BASE_MAP)

    x, y = 0, 0
    direction = "S"
    alive = True

    path = [["0" for _ in range(COLS)] for _ in range(ROWS)]
    path[x][y] = "*"

    url = f"http://127.0.0.1:8000/lab1/rover/{rover_id}"  # Change URL to local FastAPI server
    # print(f"Fetching commands for Rover {rover_id}...")  # Debug line

    # Make the GET request and handle potential key mismatches
    resp = requests.get(url)
    payload = resp.json()

    if resp.status_code != 200:
        print(f"Error: Rover {rover_id} received HTTP {resp.status_code}")
        return

    # Check for different possible response formats
    if isinstance(payload, list):
        commands = payload
    elif "moves" in payload:
        commands = payload["moves"]
    elif "commands" in payload:
        commands = payload["commands"]
    elif "data" in payload and "moves" in payload["data"]:
        commands = payload["data"]["moves"]
    else:
        raise ValueError(f"Unknown rover response format: {payload}")

    last_command = None

    for cmd in commands:
        if not alive:
            break

        if cmd == "L":
            direction = turn_left(direction)

        elif cmd == "R":
            direction = turn_right(direction)

        elif cmd == "D":
            # Dig current cell
            if land[x][y] == "1":
                land[x][y] = "0"

        elif cmd == "M":
            dx, dy = MOVE[direction]
            nx, ny = x + dx, y + dy

            # Boundary check
            if nx < 0 or nx >= ROWS or ny < 0 or ny >= COLS:
                continue

            # Mine check
            if land[nx][ny] == "1":
                if last_command == "D":
                    land[nx][ny] = "0"
                else:
                    alive = False
                    break

            x, y = nx, ny
            path[x][y] = "*"

        last_command = cmd

    # Write path file
    with open(f"path_{rover_id}.txt", "w") as f:
        for row in path:
            f.write(" ".join(row) + "\n")

# =========================
# PART 1 — SEQUENTIAL
# =========================

def run_sequential():
    start = time.time()
    for rover_id in range(1, 11):
        run_rover(rover_id)
    end = time.time()
    return end - start

# =========================
# PART 1 — THREADED
# =========================

def run_threaded():
    threads = []
    start = time.time()

    for rover_id in range(1, 11):
        t = threading.Thread(target=run_rover, args=(rover_id,))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    end = time.time()
    return end - start

# =========================
# MAIN
# =========================

if __name__ == "__main__":
    seq_time = run_sequential()
    print(f"Sequential Time: {seq_time:.4f} seconds")

    thread_time = run_threaded()
    print(f"Threaded Time:   {thread_time:.4f} seconds")

    print(f"Time Difference: {seq_time - thread_time:.4f} seconds")
