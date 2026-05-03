import grpc
from concurrent import futures
import time
import copy
import hashlib
import threading

import rover_pb2
import rover_pb2_grpc

import pika  # RabbitMQ client

# ---------- MAP / MINES REUSE FROM LAB 1 ----------

def read_map(filename="map1.txt"):
    with open(filename, "r") as f:
        first_line = f.readline().strip().split()
        rows, cols = int(first_line[0]), int(first_line[1])
        land = []
        for _ in range(rows):
            land.append([int(x) for x in f.readline().strip().split()])
    return rows, cols, land

ROWS, COLS, BASE_MAP = read_map("map1.txt")

def load_mines(filename="mines.txt"):
    mines = []
    with open(filename, "r") as f:
        for line in f:
            serial = line.strip()
            if serial:
                mines.append(serial)
    return mines

MINES = load_mines("mines.txt")

def get_mine_positions(land):
    positions = []
    for r in range(len(land)):
        for c in range(len(land[0])):
            if land[r][c] == 1:
                positions.append((r, c))
    return positions

MINE_POSITIONS = get_mine_positions(BASE_MAP)

MINE_SERIAL_MAP = {}
for idx, (r, c) in enumerate(MINE_POSITIONS):
    if idx < len(MINES):
        MINE_SERIAL_MAP[(r, c)] = MINES[idx]
    else:
        MINE_SERIAL_MAP[(r, c)] = f"EXTRA-{idx}"

# ---------- COMMANDS FOR EACH ROVER ----------

def load_rover_commands(rover_id: int) -> str:
    import random
    random.seed(rover_id)
    # In Lab 3, you *won’t* use D on the rover side, but server can still generate it
    commands = ["L", "R", "M", "D"]
    seq = "".join(random.choice(commands) for _ in range(20))
    return seq

# ---------- VERIFY PIN FUNCTION (still usable if needed) ----------

def verify_pin(pin, serial):
    temp_key = str(pin) + serial
    h = hashlib.sha256(temp_key.encode()).hexdigest()
    return h.startswith("000000")

# ---------- RABBITMQ CONSUMER FOR DEFUSED-MINES ----------

def defused_callback(ch, method, properties, body):
    pin = body.decode()
    print(f"[GROUND CONTROL] Defused mine PIN received: {pin}")

def start_defused_consumer():
    """
    Subscribe to the 'Defused-Mines' queue and print any received PINs.
    """
    connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
    channel = connection.channel()
    channel.queue_declare(queue="Defused-Mines")

    channel.basic_consume(
        queue="Defused-Mines",
        on_message_callback=defused_callback,
        auto_ack=True,
    )

    print("[GROUND CONTROL] Waiting for defused mines on 'Defused-Mines' queue...")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
        connection.close()

# ---------- SERVICE IMPLEMENTATION ----------

class RoverControlServicer(rover_pb2_grpc.RoverControlServicer):
    def GetMap(self, request, context):
        land = copy.deepcopy(BASE_MAP)
        flat = []
        for r in range(ROWS):
            for c in range(COLS):
                flat.append(land[r][c])
        map_data = rover_pb2.MapData(
            rows=ROWS,
            cols=COLS,
            data=flat
        )
        return rover_pb2.MapResponse(map=map_data)

    def GetCommands(self, request, context):
        rover_id = request.rover_id
        sequence = load_rover_commands(rover_id)
        for ch in sequence:
            yield rover_pb2.Command(cmd=ch)

    def GetMineSerial(self, request, context):
        key = (request.row, request.col)
        serial = MINE_SERIAL_MAP.get(key, "")
        return rover_pb2.MineSerialResponse(serial=serial)

    # You may keep these or ignore them for Lab 3 if not needed
    def ReportExecutionStatus(self, request, context):
        rover_id = request.rover_id
        success = request.success
        msg = request.message
        print(f"[SERVER] Rover {rover_id} finished. Success={success}, msg={msg}")
        return rover_pb2.ExecutionStatusResponse(ack=True)

    def SubmitMinePin(self, request, context):
        rover_id = request.rover_id
        serial = request.serial
        pin = request.pin

        print(f"[SERVER] Rover {rover_id} submitted PIN {pin} for mine {serial}")

        valid = verify_pin(pin, serial)

        if valid:
            print(f"[SERVER] PIN verified correct!")
        else:
            print(f"[SERVER] PIN invalid!")

        return rover_pb2.MinePinResponse(accepted=valid)

# ---------- SERVER BOOTSTRAP ----------

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    rover_pb2_grpc.add_RoverControlServicer_to_server(
        RoverControlServicer(), server
    )

    server.add_insecure_port("[::]:50051")
    server.start()
    print("RoverControl gRPC server running on port 50051...")

    # Start RabbitMQ consumer in a background thread
    consumer_thread = threading.Thread(
        target=start_defused_consumer,
        daemon=True
    )
    consumer_thread.start()

    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == "__main__":
    serve()
