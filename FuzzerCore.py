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
        # FIX 1: Dynamic Length Selection
        # Alternates between precise short payloads and large buffer smashers
        if random.random() < 0.4:
            dynamic_length = random.randint(32, 128)  # Guarantees buffer overflows (>16 bytes)
        else:
            dynamic_length = random.randint(4, 12)    # Small payloads for precise logical bugs
        
        if len(seed) > 0:
            base_data = (seed * (dynamic_length // len(seed) + 1))[:dynamic_length]
        else:
            base_data = b"A" * dynamic_length
            
        mutated = bytearray(base_data)
        
        if len(mutated) > 0:
            # FIX 2: Enhanced crash trigger dictionary
            crash_triggers = [0x00, 0xff, 0x7f, 0x80, 0x20, 0x41, 0x0a]
            
            # FIX 3: Multi-byte mutation density
            # Mutates multiple indexes per round so the search space resolves much faster
            num_mutations = random.randint(1, min(3, len(mutated)))
            for _ in range(num_mutations):
                idx = random.randint(0, len(mutated) - 1)
                mutated[idx] = random.choice(crash_triggers)
            
        # If Transparent mode is active, return raw bytes untouched
        if self.profile.transparent:
            return bytes(mutated)
            
        # Standard Profile: Apply XOR styling safely
        encrypted = bytearray(b ^ self.profile.xor_key for b in mutated)
        return self.profile.magic_bytes + encrypted

    def send_to_agent(self, payload: bytes) -> dict:
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2) 
            sock.connect((self.agent_ip, self.agent_port))
            sock.sendall(len(payload).to_bytes(4, byteorder='big'))
            sock.sendall(payload)
            response = sock.recv(4096)
            return json.loads(response.decode('utf-8'))
        except Exception as e:
            # Catches dropped connection gracefully when the binary terminates mid-packet
            return {"status": "network_error", "reason": str(e)}
        finally:
            # FIX 4: Protected resource cleanup
            if sock is not None:
                sock.close()