import socket
import random
import json

class AdversaryProfile:
    def __init__(self, name="APT-Default", magic_bytes=b"\x4d\x5a", xor_key=0x55, transparent=False):
        self.name = name
        self.magic_bytes = magic_bytes
        self.xor_key = xor_key
        self.transparent = transparent

class CoreEngine:
    def __init__(self, agent_ip, agent_port, profile: AdversaryProfile):
        self.agent_ip = agent_ip
        self.agent_port = agent_port
        self.profile = profile

    def mutate_and_style(self, seed: bytes) -> bytes:
        # Dynamically vary the buffer length to catch stack overflows
        # Alternates lengths between 8 bytes and 128 bytes
        dynamic_length = random.randint(8, 128)
        
        if len(seed) > 0:
            # Resize or pad the seed to create variable length structures
            base_data = (seed * (dynamic_length // len(seed) + 1))[:dynamic_length]
        else:
            base_data = b"A" * dynamic_length
            
        mutated = bytearray(base_data)
        
        if len(mutated) > 0:
            idx = random.randint(0, len(mutated) - 1)
            # Expanded dictionary containing edge-cases, nulls, and space characters (0x20)
            mutated[idx] = random.choice([0x00, 0xff, 0x7f, 0x80, 0x20, 0x41])
            
        # If the transparent profile is active, bypass headers and encryption entirely
        if self.profile.transparent:
            return bytes(mutated)
            
        encrypted = bytearray(b ^ self.profile.xor_key for b in mutated)
        return self.profile.magic_bytes + encrypted

    def send_to_agent(self, payload: bytes) -> dict:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3) 
            sock.connect((self.agent_ip, self.agent_port))
            sock.sendall(len(payload).to_bytes(4, byteorder='big'))
            sock.sendall(payload)
            response = sock.recv(4096)
            return json.loads(response.decode('utf-8'))
        except Exception as e:
            return {"status": "network_error", "reason": str(e)}
        finally:
            sock.close()