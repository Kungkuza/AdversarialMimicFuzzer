import socket
import random
import json
import time

TARGET_AGENT_IP = '192.168.56.102'  #placeholder agent IP
TARGET_AGENT_PORT = 9999

class AdversaryProfile:
    def __init__(self):
        self.magic_bytes = b"\x4d\x5a"
        self.xor_key = 0x55

def mutate_and_style(seed: bytes, profile: AdversaryProfile) -> bytes:
    """Mutates seed data and wraps it in the adversary's signature."""
    mutated = bytearray(seed)
    if len(mutated) > 0:
        #Flip a random byte
        idx = random.randint(0, len(mutated) - 1)
        mutated[idx] = random.choice([0x00, 0xff, 0x7f, 0x80])
        
    #Apply adversary encryption wrapper
    encrypted = bytearray(b ^ profile.xor_key for b in mutated)
    return profile.magic_bytes + encrypted

def send_payload_to_agent(payload: bytes) -> dict:
    """Streams the payload to the remote agent and awaits telemetry."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((TARGET_AGENT_IP, TARGET_AGENT_PORT))
        
        #Send length prefix followed by payload
        sock.sendall(len(payload).to_bytes(4, byteorder='big'))
        sock.sendall(payload)
        
        #report
        response = sock.recv(4096)
        return json.loads(response.decode('utf-8'))
    except Exception as e:
        return {"status": "network_error", "reason": str(e)}
    finally:
        sock.close()

def main():
    profile = AdversaryProfile()
    base_seed = b"normal_agent_traffic_data"
    iterations = 100
    
    print(f"[*] Starting Adversary Fuzzing Campaign against Agent {TARGET_AGENT_IP}...")
    
    for i in range(iterations):
        payload = mutate_and_style(base_seed, profile)
        
        report = send_payload_to_agent(payload)
        
        if report.get("status") == "crash":
            print(f"\n[!] ALERT: Target Agent crashed on iteration {i}!")
            print(f"    Reason: {report.get('reason')}")
            print(f"    Payload Sent (Hex): {payload.hex()}")
            break
        elif report.get("status") == "network_error":
            print(f"\n[!] Lost connection to agent: {report.get('reason')}. Target might have bluescreened/hard-crashed!")
            break
        
        if i % 10 == 0:
            print(f"[*] Sent {i} payloads... Agent is still alive and responsive.")
            
if __name__ == "__main__":
    main()