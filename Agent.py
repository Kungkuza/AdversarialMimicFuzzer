import socket
import subprocess
import json

AGENT_HOST = '0.0.0.0'
AGENT_PORT = 9999

def execute_and_monitor(payload: bytes) -> dict:
    filename = "tmp_payload.bin"
    with open(filename, "wb") as f:
        f.write(payload)
        
    try:
        target_binary = "./div-zero"
        # Runs inline python target. It will exit with code 1 if b'\xff\xff' is generated.
        result = subprocess.run(
            [target_binary, payload.decode('utf-8', errors='ignore')], 
            capture_output=True,
        text=True, 
            timeout=2
        )
        
        # FIX: Check if the sub-process returned an error code (like 1 from AssertionError)
        if result.returncode != 0:
            return {
                "status": "crash",
                "reason": "Target process returned non-zero status (Assertion/Crash triggered!)",
                "return_code": result.returncode,
                "stderr": result.stderr.decode(errors='ignore')
            }
        
        return {
            "status": "success",
            "return_code": result.returncode,
            "stdout": result.stdout.decode(errors='ignore'),
            "stderr": result.stderr.decode(errors='ignore')
        }
    except subprocess.TimeoutExpired:
        return {"status": "crash", "reason": "Target process hung (TimeoutExpired)"}
    except Exception as e:
        return {"status": "error", "reason": str(e)}

def start_agent():
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Allows rapid restarting
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((AGENT_HOST, AGENT_PORT))
    server_sock.listen(5)
    print(f"[*] Agent listening on {AGENT_HOST}:{AGENT_PORT}...")

    while True:
        client_sock, addr = server_sock.accept()
        try:
            payload_len_bytes = client_sock.recv(4)
            if not payload_len_bytes: continue
            payload_len = int.from_bytes(payload_len_bytes, byteorder='big')
            
            payload = b""
            while len(payload) < payload_len:
                packet = client_sock.recv(payload_len - len(payload))
                if not packet: break
                payload += packet
                
            print(f"[+] Received {len(payload)} bytes from Fuzzer at {addr[0]}")
            
            telemetry = execute_and_monitor(payload)
            response_data = json.dumps(telemetry).encode('utf-8')
            client_sock.sendall(response_data)
            
        except Exception as e:
            print(f"[!] Error handling request: {e}")
        finally:
            client_sock.close()

if __name__ == "__main__":
    start_agent()
