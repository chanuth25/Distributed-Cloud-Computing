import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def print_json(response):
    if isinstance(response, requests.Response):
        if response.ok:
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Error {response.status_code}: {response.text}")
    else:
        print(json.dumps(response, indent=2))

def print_map(data):
    for row in data["data"]:
        print(' '.join(map(str, row)))

def get_map():
    resp = requests.get(f"{BASE_URL}/map")
    print("Current Map:")
    if resp.ok:
        print_map(resp.json())
    else:
        print_json(resp)

def update_map(rows=10, cols=10):
    resp = requests.put(f"{BASE_URL}/map", params={"rows": rows, "cols": cols})
    print_json(resp)

def list_mines():
    print_json(requests.get(f"{BASE_URL}/mines"))

def get_mine(id):
    print_json(requests.get(f"{BASE_URL}/mines/{id}"))

def create_mine(serial, x, y):
    print_json(requests.post(f"{BASE_URL}/mines", json={
        "serial": serial, "x": x, "y": y
    }))

def delete_mine(id):
    print_json(requests.delete(f"{BASE_URL}/mines/{id}"))

def update_mine(id, serial=None, x=None, y=None):
    data = {k: v for k, v in {
        "serial": serial, "x": x, "y": y
    }.items() if v is not None}
    print_json(requests.put(f"{BASE_URL}/mines/{id}", json=data))

def list_rovers():
    print_json(requests.get(f"{BASE_URL}/rovers"))

def get_rover(id):
    print_json(requests.get(f"{BASE_URL}/rovers/{id}"))

def create_rover(commands):
    print_json(requests.post(f"{BASE_URL}/rovers", json={
        "commands": commands
    }))

def delete_rover(id):
    print_json(requests.delete(f"{BASE_URL}/rovers/{id}"))

def set_rover_commands(id, commands):
    print_json(requests.put(f"{BASE_URL}/rovers/{id}", json={
        "commands": commands
    }))

def dispatch_rover(id):
    resp = requests.post(f"{BASE_URL}/rovers/{id}/dispatch")
    print_json(resp)

    if resp.ok and "path" in resp.json():
        print("Rover Path:")
        for row in resp.json()["path"]:
            print(" ".join(row))

def main():
    print("Operator running...")

    while True:
        print("\n1.Map 2.Mines 3.Rovers 4.Exit")
        choice = input("> ")

        if choice == "1":
            get_map()

        elif choice == "2":
            print("l=list c=create d=delete u=update")
            sub = input("> ")

            if sub == "l":
                list_mines()
            elif sub == "c":
                create_mine(input("serial: "), int(input("x: ")), int(input("y: ")))
            elif sub == "d":
                delete_mine(int(input("id: ")))
            elif sub == "u":
                id = int(input("id: "))
                update_mine(id)

        elif choice == "3":
            print("l=list c=create s=set p=dispatch")
            sub = input("> ")

            if sub == "l":
                list_rovers()
            elif sub == "c":
                create_rover(input("commands: "))
            elif sub == "s":
                set_rover_commands(int(input("id: ")), input("commands: "))
            elif sub == "p":
                dispatch_rover(int(input("id: ")))

        elif choice == "4":
            break

if __name__ == "__main__":
    main()
