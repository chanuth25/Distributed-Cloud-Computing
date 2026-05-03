import grpc
import rover_pb2
import rover_pb2_grpc

def test_server():
    channel = grpc.insecure_channel("localhost:50051")
    stub = rover_pb2_grpc.RoverControlStub(channel)

    print("Testing GetMap...")
    try:
        map_resp = stub.GetMap(rover_pb2.MapRequest(rover_id=1))
        print(f"  PASS: Map size {map_resp.map.rows}x{map_resp.map.cols}")
        print(f"  PASS: First 10 cells: {map_resp.map.data[:10]}")
    except Exception as e:
        print(f"  FAIL: {e}")

    print("Testing GetCommands...")
    try:
        cmds = stub.GetCommands(rover_pb2.CommandRequest(rover_id=1))
        cmd_count = 0
        for cmd in cmds:
            print(f"  Cmd {cmd_count}: {cmd.cmd}")
            cmd_count += 1
            if cmd_count >= 5:
                break
        print(f"  PASS: Received {cmd_count} commands")
    except Exception as e:
        print(f"  FAIL: {e}")

    print("Testing GetMineSerial...")
    try:
        serial_resp = stub.GetMineSerial(rover_pb2.MineSerialRequest(rover_id=1, row=1, col=2))
        print(f"  PASS: Serial = '{serial_resp.serial}'")
    except Exception as e:
        print(f"  FAIL: {e}")

    print("Testing SubmitMinePin...")
    try:
        pin_resp = stub.SubmitMinePin(rover_pb2.MinePinRequest(rover_id=1, serial="TEST123", pin=0))
        print(f"  PASS: Server accepted = {pin_resp.accepted}")
    except Exception as e:
        print(f"  FAIL: {e}")

    print("Testing ReportExecutionStatus...")
    try:
        status_resp = stub.ReportExecutionStatus(rover_pb2.ExecutionStatusRequest(rover_id=1, success=True, message="Test OK"))
        print(f"  PASS: ACK = {status_resp.ack}")
    except Exception as e:
        print(f"  FAIL: {e}")

    print("" + "="*50)
    print("SERVER TEST SUMMARY: Run this with server running!")
    print("="*50)

if __name__ == "__main__":
    test_server()