import grpc
import sys
import copy
import hashlib

import rover_pb2
import rover_pb2_grpc

# Directions and movement (from Lab 1)
DIRECTIONS = ["N", "E", "S", "W"]
MOVE = {
    "N": (-1, 0),
    "E": (0, 1),
    "S": (1, 0),
    "W": (0, -1),
}

def turn_left(d):
    return DIRECTIONS[(DIRECTIONS.index(d) - 1) % 4]

def turn_right(d):
    return DIRECTIONS[(DIRECTIONS.index(d) + 1) % 4]

def build_map_from_response(map_resp):
    rows = map_resp.map.rows
    cols = map_resp.map.cols
    flat = list(map_resp.map.data)
    land = []
    idx = 0
    for r in range(rows):
        row = []
        for c in range(cols):
            row.append(flat[idx])
            idx += 1
        land.append(row)
    return rows, cols, land

# YOUR disarm_mine from part2.py
def disarm_mine(serial):
    pin = 0
    while True:
        temp_key = str(pin) + serial
        h = hashlib.sha256(temp_key.encode()).hexdigest()
        if h.startswith("000000"):
            print(f"[ROVER] Disarmed mine {serial} with PIN {pin}")
            return pin, h
        pin += 1

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 client_complete.py <rover_id>")
        sys.exit(1)

    rover_id = int(sys.argv[1])

    channel = grpc.insecure_channel("localhost:50051")
    stub = rover_pb2_grpc.RoverControlStub(channel)

    # 1. Get map
    print(f"[ROVER {rover_id}] Getting map...")
    map_resp = stub.GetMap(rover_pb2.MapRequest(rover_id=rover_id))
    ROWS, COLS, land = build_map_from_response(map_resp)
    land = copy.deepcopy(land)

    # Initial state
    x, y = 0, 0
    direction = "S"
    alive = True
    last_command = None

    print(f"[ROVER {rover_id}] Starting at ({x},{y}), facing {direction}")

    # 2. Get command stream
    print(f"[ROVER {rover_id}] Getting commands...")
    cmd_stream = stub.GetCommands(rover_pb2.CommandRequest(rover_id=rover_id))

    for cmd_msg in cmd_stream:
        cmd = cmd_msg.cmd

        if not alive:
            break

        if cmd == "L":
            direction = turn_left(direction)
            print(f"[ROVER {rover_id}] Turn LEFT -> {direction}")

        elif cmd == "R":
            direction = turn_right(direction)
            print(f"[ROVER {rover_id}] Turn RIGHT -> {direction}")

        elif cmd == "D":
            if land[x][y] == 1:
                land[x][y] = 0
                print(f"[ROVER {rover_id}] Digged current cell ({x},{y})")

        elif cmd == "M":
            dx, dy = MOVE[direction]
            nx, ny = x + dx, y + dy

            if nx < 0 or nx >= ROWS or ny < 0 or ny >= COLS:
                print(f"[ROVER {rover_id}] Boundary hit, staying at ({x},{y})")
                continue

            if land[nx][ny] == 1:
                print(f"[ROVER {rover_id}] Mine detected at ({nx},{ny})")

                # Get serial
                ms_req = rover_pb2.MineSerialRequest(rover_id=rover_id, row=nx, col=ny)
                ms_resp = stub.GetMineSerial(ms_req)
                serial = ms_resp.serial
                print(f"[ROVER {rover_id}] Got serial: {serial}")

                # BRUTE-FORCE YOUR PIN
                pin, hash_value = disarm_mine(serial)

                # Submit to server
                pin_resp = stub.SubmitMinePin(
                    rover_pb2.MinePinRequest(rover_id=rover_id, serial=serial, pin=pin)
                )
                print(f"[ROVER {rover_id}] Server response: {pin_resp.accepted}")

                land[nx][ny] = 0

            x, y = nx, ny
            print(f"[ROVER {rover_id}] Moved to ({x},{y})")

        last_command = cmd

    # 4. Report status
    status_req = rover_pb2.ExecutionStatusRequest(
        rover_id=rover_id,
        success=alive,
        message="All commands executed" if alive else "Destroyed by mine"
    )
    stub.ReportExecutionStatus(status_req)

    print(f"[ROVER {rover_id}] FINISHED. Alive={alive}, pos=({x},{y}), dir={direction}")

if __name__ == "__main__":
    main()