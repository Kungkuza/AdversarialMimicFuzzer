import socket
import subprocess
import json

AGENT_HOST = '0.0.0.0'
AGENT_PORT = 9999

def execute_and_monitor(payload: bytes) -> dict:
    """
    Simulates executing the adversary payload or passing it to a local binary.
    Returns telemetry back to the fuzzer.
    """
    # Write payload to a temporary file for local execution/parsing
    filename = "tmp_payload.bin"
    with open(filename, "wb") as f:
        f.write(payload)
        
    try:
        # Simulating passing the payload to a monitored target application
        # Replace 'python3 mockup_app.py' with your actual target binary
        result = subprocess.run(
            ["python3", "-c", f"import sys; data=open('{filename}', 'rb').read(); assert b'\\xff\\xff' not in data"], 
            capture_output=True, 
            timeout=2
        )
        
        return {
            "status": "success",
            "return_code": result.returncode,
            "stdout": result.stdout.decode(errors='ignore'),
            "stderr": result.stderr.decode(errors='ignore')
        }
    except subprocess.CalledProcessError as e:
        return {"status": "crash", "reason": "Process returned non-zero exit code"}
    except AssertionError:
        return {"status": "crash", "reason": "Assertion triggered - Vulnerability hit!"}
    except Exception as e:
        return {"status": "error", "reason": str(e)}

def start_agent():
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind((AGENT_HOST, AGENT_PORT))
    server_sock.listen(5)
    print(f"[*] Agent listening on {AGENT_HOST}:{AGENT_PORT}...")

    while True:
        client_sock, addr = server_sock.accept()
        # Receive the size prefix first (4 bytes)
        try:
            payload_len_bytes = client_sock.recv(4)
            if not payload_len_bytes: continue
            payload_len = int.from_bytes(payload_len_bytes, byteorder='big')
            
            # Read the actual payload
            payload = b""
            while len(payload) < payload_len:
                packet = client_sock.recv(payload_len - len(payload))
                if not packet: break
                payload += packet
                
            print(f"[+] Received {len(payload)} bytes from Fuzzer at {addr[0]}")
            
            # Run test and send back telemetry
            telemetry = execute_and_monitor(payload)
            response_data = json.dumps(telemetry).encode('utf-8')
            client_sock.sendall(response_data)
            
        except Exception as e:
            print(f"[!] Error handling request: {e}")
        finally:
            client_sock.close()

if __name__ == "__main__":
    start_agent()