import sys
import pika
import json
import hashlib
import threading
import time


def compute_pin(serial: str) -> int:
    """
    Brute-force PIN like Lab 2 part2.py (6 leading zero SHA256).
    """
    pin = 0
    while True:
        temp_key = f"{pin}{serial}"
        h = hashlib.sha256(temp_key.encode()).hexdigest()
        if h.startswith("000000"):
            print(f"[DEMINER] Disarmed mine {serial} with PIN {pin}")
            return pin
        pin += 1


def deminer_worker(deminer_id: str):
    """
    Deminer subscribes to Demine-Queue, processes one mine at a time (if not busy),
    publishes PIN to Defused-Mines.
    """
    defused_connection = None  # For publishing

    def callback(ch, method, properties, body):
        nonlocal defused_connection

        try:
            task = json.loads(body.decode())
            row = task["row"]
            col = task["col"]
            mine_id = task["mine_id"]
            serial = task["serial"]

            print(f"[DEMINER {deminer_id}] Assigned mine #{mine_id} at ({row},{col}), serial {serial}")

            # Simulate "demining time" (not busy during this)
            print(f"[DEMINER {deminer_id}] Demining... (computing PIN)")
            time.sleep(1)  # Brief delay to simulate work

            pin = compute_pin(serial)

            # Publish PIN to Defused-Mines for ground control
            if defused_connection is None or defused_connection.is_closed:
                defused_connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))

            defused_channel = defused_connection.channel()
            defused_channel.queue_declare(queue="Defused-Mines")

            defused_channel.basic_publish(
                exchange="",
                routing_key="Defused-Mines",
                body=str(pin).encode()
            )
            print(f"[DEMINER {deminer_id}] Published PIN {pin} to Defused-Mines queue")

            defused_channel.close()

            print(f"[DEMINER {deminer_id}] Completed mine #{mine_id}")
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            print(f"[DEMINER {deminer_id}] Error processing task: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    # Main connection to Demine-Queue
    connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
    channel = connection.channel()
    channel.queue_declare(queue="Demine-Queue")

    # Fair dispatch: only give 1 message at a time per deminer (simulates "not busy")
    channel.basic_qos(prefetch_count=1)

    channel.basic_consume(
        queue="Demine-Queue",
        on_message_callback=callback,
        auto_ack=False  # Manual ack after successful processing
    )

    print(f"[DEMINER {deminer_id}] Started and listening to Demine-Queue (prefetch=1)...")
    print(f"[DEMINER {deminer_id}] Ready for mine disarming tasks!")

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print(f"[DEMINER {deminer_id}] Shutting down...")
        channel.stop_consuming()
        connection.close()
        if defused_connection and not defused_connection.is_closed:
            defused_connection.close()


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ["1", "2"]:
        print("Usage: python deminer.py [1|2]")
        sys.exit(1)

    deminer_id = sys.argv[1]
    deminer_worker(deminer_id)
