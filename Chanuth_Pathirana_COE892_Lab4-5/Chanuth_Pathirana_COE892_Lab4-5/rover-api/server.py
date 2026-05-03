from fastapi import FastAPI, HTTPException, Path, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import copy
import uvicorn

app = FastAPI(title="Rover Demining Server")

# -------------------------
# DATA
# -------------------------
MAP_ROWS, MAP_COLS = 10, 10
land_map = [[0 for _ in range(MAP_COLS)] for _ in range(MAP_ROWS)]
mines: List[Dict[str, Any]] = []
rovers: Dict[int, Dict[str, Any]] = {}

# -------------------------
# MODELS
# -------------------------
class MineCreate(BaseModel):
    serial: str
    x: int
    y: int

class MineUpdate(BaseModel):
    serial: Optional[str] = None
    x: Optional[int] = None
    y: Optional[int] = None

class RoverCreate(BaseModel):
    commands: str

# -------------------------
# ROVER LOGIC (Lab 2)
# -------------------------
DIRECTIONS = ['N', 'E', 'S', 'W']
MOVE = {'N': (-1, 0), 'E': (0, 1), 'S': (1, 0), 'W': (0, -1)}

def turn_left(direction):
    return DIRECTIONS[(DIRECTIONS.index(direction) - 1) % 4]

def turn_right(direction):
    return DIRECTIONS[(DIRECTIONS.index(direction) + 1) % 4]

def execute_rover_commands(commands: str):
    rover_land = copy.deepcopy(land_map)
    x, y = 0, 0
    direction = 'S'
    alive = True

    path = [['.' for _ in range(MAP_COLS)] for _ in range(MAP_ROWS)]
    path[x][y] = '*'

    executed = []

    for cmd in commands:
        if not alive:
            break

        if cmd == 'L':
            direction = turn_left(direction)

        elif cmd == 'R':
            direction = turn_right(direction)

        elif cmd == 'D':
            if rover_land[x][y] == 1:
                rover_land[x][y] = 0

        elif cmd == 'M':
            dx, dy = MOVE[direction]
            nx, ny = x + dx, y + dy

            # bounds check
            if nx < 0 or nx >= MAP_ROWS or ny < 0 or ny >= MAP_COLS:
                continue

            # hit mine → eliminated
            if rover_land[nx][ny] == 1:
                alive = False
                break

            x, y = nx, ny

        path[x][y] = '*'
        executed.append(cmd)

    return {
        "status": "Finished" if alive else "Eliminated",
        "position": {"x": x, "y": y},
        "executed_commands": executed,
        "path": path
    }

# -------------------------
# HELPERS
# -------------------------
def update_map_from_mines():
    for r in range(MAP_ROWS):
        for c in range(MAP_COLS):
            land_map[r][c] = 0
    for m in mines:
        if 0 <= m["x"] < MAP_ROWS and 0 <= m["y"] < MAP_COLS:
            land_map[m["x"]][m["y"]] = 1

# -------------------------
# MAP ENDPOINTS
# -------------------------
def load_map_from_file():
    global land_map, MAP_ROWS, MAP_COLS

    with open("map.txt", "r") as f:
        lines = f.readlines()

    grid = []
    for line in lines:
        row = list(map(int, line.strip().split()))
        grid.append(row)

    land_map = grid
    MAP_ROWS = len(grid)
    MAP_COLS = len(grid[0]) if grid else 0

@app.get("/map")
def get_map():
    load_map_from_file()
    return {"rows": MAP_ROWS, "cols": MAP_COLS, "data": land_map}

@app.put("/map")
def update_map(rows: int = Query(10), cols: int = Query(10)):
    global MAP_ROWS, MAP_COLS, land_map

    MAP_ROWS, MAP_COLS = rows, cols
    land_map = [[0 for _ in range(cols)] for _ in range(rows)]

    # remove out-of-bounds mines
    mines[:] = [m for m in mines if 0 <= m["x"] < rows and 0 <= m["y"] < cols]

    update_map_from_mines()
    return {"message": f"Map updated to {rows}x{cols}"}

# -------------------------
# MINES
# -------------------------
@app.get("/mines")
def get_mines():
    return mines

@app.get("/mines/{mine_id}")
def get_mine(mine_id: int = Path(..., ge=1)):
    mine = next((m for m in mines if m["id"] == mine_id), None)
    if not mine:
        raise HTTPException(404, "Mine not found")
    return mine

@app.post("/mines", status_code=201)
def create_mine(mine: MineCreate):
    if not (0 <= mine.x < MAP_ROWS and 0 <= mine.y < MAP_COLS):
        raise HTTPException(400, "Mine coordinates out of bounds")

    mine_id = max([m["id"] for m in mines] + [0]) + 1
    new_mine = {"id": mine_id, "serial": mine.serial, "x": mine.x, "y": mine.y}
    mines.append(new_mine)

    update_map_from_mines()
    return {"id": mine_id}

@app.put("/mines/{mine_id}")
def update_mine(mine_id: int, mine_update: MineUpdate):
    mine = next((m for m in mines if m["id"] == mine_id), None)
    if not mine:
        raise HTTPException(404, "Mine not found")

    if mine_update.serial is not None:
        mine["serial"] = mine_update.serial
    if mine_update.x is not None:
        mine["x"] = mine_update.x
    if mine_update.y is not None:
        mine["y"] = mine_update.y

    if not (0 <= mine["x"] < MAP_ROWS and 0 <= mine["y"] < MAP_COLS):
        raise HTTPException(400, "Mine coordinates out of bounds")

    update_map_from_mines()
    return mine

@app.delete("/mines/{mine_id}")
def delete_mine(mine_id: int):
    mine = next((m for m in mines if m["id"] == mine_id), None)
    if not mine:
        raise HTTPException(404, "Mine not found")

    mines.remove(mine)
    update_map_from_mines()
    return {"message": "Mine deleted"}

# -------------------------
# ROVERS
# -------------------------
@app.get("/rovers")
def get_rovers():
    return [{"id": rid, "status": r["status"]} for rid, r in rovers.items()]

@app.get("/rovers/{rover_id}")
def get_rover(rover_id: int):
    rover = rovers.get(rover_id)
    if not rover:
        raise HTTPException(404, "Rover not found")
    return rover

@app.post("/rovers", status_code=201)
def create_rover(rover: RoverCreate):
    rover_id = max(rovers.keys(), default=0) + 1
    rovers[rover_id] = {
        "status": "Not Started",
        "commands": rover.commands,
        "position": {"x": 0, "y": 0},
        "executed_commands": []
    }
    return {"id": rover_id}

@app.put("/rovers/{rover_id}")
def set_commands(rover_id: int, rover: RoverCreate):
    if rover_id not in rovers:
        raise HTTPException(404, "Rover not found")

    if rovers[rover_id]["status"] not in ["Not Started", "Finished"]:
        raise HTTPException(400, "Rover is busy")

    rovers[rover_id]["commands"] = rover.commands
    rovers[rover_id]["status"] = "Not Started"
    return {"message": "Commands updated"}

@app.delete("/rovers/{rover_id}")
def delete_rover(rover_id: int):
    if rover_id not in rovers:
        raise HTTPException(404, "Rover not found")

    del rovers[rover_id]
    return {"message": "Rover deleted"}

@app.post("/rovers/{rover_id}/dispatch")
def dispatch_rover(rover_id: int):
    if rover_id not in rovers:
        raise HTTPException(404, "Rover not found")

    rover = rovers[rover_id]

    if rover["status"] != "Not Started":
        raise HTTPException(400, "Can only dispatch Not Started rover")

    result = execute_rover_commands(rover["commands"])

    rover["status"] = result["status"]
    rover["position"] = result["position"]
    rover["executed_commands"] = result["executed_commands"]

    # remove destroyed mines
    update_map_from_mines()

    return {
        "id": rover_id,
        "status": rover["status"],
        "position": rover["position"],
        "executed_commands": rover["executed_commands"],
        "path": result["path"]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
