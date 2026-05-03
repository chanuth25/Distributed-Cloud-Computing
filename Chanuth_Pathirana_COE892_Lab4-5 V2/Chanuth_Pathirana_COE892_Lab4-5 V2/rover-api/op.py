import json
import requests

BASE_URL = "http://127.0.0.1:8000"


def print_response(response):
    try:
        data = response.json()
    except Exception:
        print(f"Error {response.status_code}: {response.text}")
        return

    if response.ok:
        print(json.dumps(data, indent=2))
    else:
        print(f"Error {response.status_code}:")
        print(json.dumps(data, indent=2))


def print_map_payload(payload):
    print(f"Map: {payload['rows']} x {payload['cols']}")
    for row in payload["data"]:
        print(" ".join(str(cell) for cell in row))


def get_map():
    response = requests.get(f"{BASE_URL}/map")
    if response.ok:
        print_map_payload(response.json())
    else:
        print_response(response)


def resize_map():
    rows = int(input("rows: "))
    cols = int(input("cols: "))
    response = requests.put(f"{BASE_URL}/map", params={"rows": rows, "cols": cols})
    print_response(response)


def list_mines():
    print_response(requests.get(f"{BASE_URL}/mines"))


def get_mine():
    mine_id = int(input("mine id: "))
    print_response(requests.get(f"{BASE_URL}/mines/{mine_id}"))


def create_mine():
    serial = input("serial: ").strip()
    x = int(input("x: "))
    y = int(input("y: "))
    print_response(requests.post(f"{BASE_URL}/mines", json={"serial": serial, "x": x, "y": y}))


def update_mine():
    mine_id = int(input("mine id: "))
    serial = input("new serial (blank to keep): ").strip()
    x = input("new x (blank to keep): ").strip()
    y = input("new y (blank to keep): ").strip()

    body = {}
    if serial:
        body["serial"] = serial
    if x:
        body["x"] = int(x)
    if y:
        body["y"] = int(y)

    print_response(requests.put(f"{BASE_URL}/mines/{mine_id}", json=body))


def delete_mine():
    mine_id = int(input("mine id: "))
    print_response(requests.delete(f"{BASE_URL}/mines/{mine_id}"))


def list_rovers():
    print_response(requests.get(f"{BASE_URL}/rovers"))


def get_rover():
    rover_id = int(input("rover id: "))
    print_response(requests.get(f"{BASE_URL}/rovers/{rover_id}"))


def create_rover():
    commands = input("commands (L/R/M/D only): ").strip().upper()
    print_response(requests.post(f"{BASE_URL}/rovers", json={"commands": commands}))


def set_rover_commands():
    rover_id = int(input("rover id: "))
    commands = input("new commands (L/R/M/D only): ").strip().upper()
    print_response(requests.put(f"{BASE_URL}/rovers/{rover_id}", json={"commands": commands}))


def delete_rover():
    rover_id = int(input("rover id: "))
    print_response(requests.delete(f"{BASE_URL}/rovers/{rover_id}"))


def dispatch_rover():
    rover_id = int(input("rover id: "))
    response = requests.post(f"{BASE_URL}/rovers/{rover_id}/dispatch")
    print_response(response)

    if response.ok:
        payload = response.json()
        print("Rover Path:")
        for row in payload["path"]:
            print(" ".join(row))


def mines_menu():
    while True:
        print("\nMines Menu")
        print("1. List mines")
        print("2. Get mine by id")
        print("3. Create mine")
        print("4. Update mine")
        print("5. Delete mine")
        print("6. Back")
        choice = input("> ").strip()

        if choice == "1":
            list_mines()
        elif choice == "2":
            get_mine()
        elif choice == "3":
            create_mine()
        elif choice == "4":
            update_mine()
        elif choice == "5":
            delete_mine()
        elif choice == "6":
            return
        else:
            print("Invalid choice")


def rovers_menu():
    while True:
        print("\nRovers Menu")
        print("1. List rovers")
        print("2. Get rover by id")
        print("3. Create rover")
        print("4. Set rover commands")
        print("5. Dispatch rover")
        print("6. Delete rover")
        print("7. Back")
        choice = input("> ").strip()

        if choice == "1":
            list_rovers()
        elif choice == "2":
            get_rover()
        elif choice == "3":
            create_rover()
        elif choice == "4":
            set_rover_commands()
        elif choice == "5":
            dispatch_rover()
        elif choice == "6":
            delete_rover()
        elif choice == "7":
            return
        else:
            print("Invalid choice")


def main():
    print("Operator running...")
    while True:
        print("\nMain Menu")
        print("1. Get map")
        print("2. Update map size")
        print("3. Mines")
        print("4. Rovers")
        print("5. Exit")
        choice = input("> ").strip()

        if choice == "1":
            get_map()
        elif choice == "2":
            resize_map()
        elif choice == "3":
            mines_menu()
        elif choice == "4":
            rovers_menu()
        elif choice == "5":
            break
        else:
            print("Invalid choice")


if __name__ == "__main__":
    main()


