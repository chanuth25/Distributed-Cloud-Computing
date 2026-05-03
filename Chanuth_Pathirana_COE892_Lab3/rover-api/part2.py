import hashlib
import threading
import time

# -----------------------------
# Load mine serial numbers
# -----------------------------
def load_mines(filename="mines.txt"):
    mines = []
    with open(filename, "r") as f:
        for line in f:
            serial = line.strip()
            if serial:
                mines.append(serial)
    return mines


# -----------------------------
# Brute-force disarm function
# -----------------------------
def disarm_mine(serial):
    pin = 0
    while True:
        temp_key = str(pin) + serial
        h = hashlib.sha256(temp_key.encode()).hexdigest()

        # Check for at least six leading zeros
        if h.startswith("000000"):
            print(f"Disarmed mine with PIN {pin}")
            return pin, h

        pin += 1


# -----------------------------
# Sequential version
# -----------------------------
def sequential_disarm(mines):
    print("\n--- Sequential Disarming ---")
    results = []
    start = time.time()

    for serial in mines:
        result = disarm_mine(serial)
        results.append(result)

    end = time.time()
    total_time = end - start

    print(f"\nSequential total time: {total_time:.2f} seconds")
    return total_time, results


# -----------------------------
# Thread worker
# -----------------------------
def thread_worker(serial, results, index):
    results[index] = disarm_mine(serial)


# -----------------------------
# Threaded version
# -----------------------------
def threaded_disarm(mines):
    print("\n--- Threaded Disarming ---")
    threads = []
    results = [None] * len(mines)

    start = time.time()

    for i, serial in enumerate(mines):
        t = threading.Thread(target=thread_worker, args=(serial, results, i))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    end = time.time()
    total_time = end - start

    print(f"\nThreaded total time: {total_time:.2f} seconds")
    return total_time, results


# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    mines = load_mines("mines.txt")

    # Sequential
    seq_time, seq_results = sequential_disarm(mines)

    # Threaded
    th_time, th_results = threaded_disarm(mines)

    # Comparison
    print("\n--- Comparison ---")
    print(f"Sequential Time: {seq_time:.2f} seconds")
    print(f"Threaded Time:   {th_time:.2f} seconds")
    print(f"Time Difference: {seq_time - th_time:.2f} seconds")