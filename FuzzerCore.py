import socket
import random
import json

class AdversaryProfile:
    def __init__(self, name="APT-Default", magic_bytes=b"\x4d\x5a", xor_key=0x55):
        self.name = name
        self.magic_bytes = magic_bytes
        self.xor_key = xor_key

class CoreEngine:
    def __init__(self, agent_ip, agent_port, profile: AdversaryProfile):
        self.agent_ip = agent_ip
        self.agent_port = agent_port
        self.profile = profile

    def mutate_and_style(self, seed: bytes) -> bytes:
        mutated = bytearray(seed)
        if len(mutated) > 0:
            idx = random.randint(0, len(mutated) - 1)
            mutated[idx] = random.choice([0x00, 0xff, 0x7f, 0x80])
        encrypted = bytearray(b ^ self.profile.xor_key for b in mutated)
        return self.profile.magic_bytes + encrypted

    def send_to_agent(self, payload: bytes) -> dict:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3) # Don't hang forever
            sock.connect((self.agent_ip, self.agent_port))
            sock.sendall(len(payload).to_bytes(4, byteorder='big'))
            sock.sendall(payload)
            response = sock.recv(4096)
            return json.loads(response.decode('utf-8'))
        except Exception as e:
            return {"status": "network_error", "reason": str(e)}
        finally:
            sock.close()