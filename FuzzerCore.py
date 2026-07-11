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

    def mutate_and_style(self, seed: bytes, prefix: bytes = b"", target_type: str = "binary") -> bytes:
        """
        Comprehensive Generation and Mutation Layer.
        - prefix: Mandatory valid bytes that stay untouched to clear initial validation headers.
        - target_type: Adjusts dictionary payload behavior based on what the C binary expects.
        """
        # FIX: Context-Aware Type Generation to pass syntax filters
        if target_type == "numeric_string":
            # Boundary strings designed to break conversions like atoi() or arithmetic calculations
            numeric_triggers = ["0", "-1", "2147483647", "-2147483648", "4294967295", " ", "000000000"]
            data_zone = random.choice(numeric_triggers).encode('utf-8')
        
        elif target_type == "alphanumeric":
            # Safe printable ASCII buffers scaled dynamically to bypass binary stripping rules
            length = random.choice([8, 16, 64, 128])
            data_zone = bytes(random.choice(range(0x21, 0x7E)) for _ in range(length))
            
        else:
            # Default Binary Mode: Alternating short and long structures with intensive injection
            dynamic_length = random.choice([8, 16, 64, 128])
            base = (seed * (dynamic_length // len(seed) + 1))[:dynamic_length] if seed else b"A" * dynamic_length
            mutated = bytearray(base)
            
            # FIX: High density multi-byte mutations
            crash_triggers = [0x00, 0xff, 0x7f, 0x80, 0x20, 0x0a]
            num_mutations = random.randint(1, min(3, len(mutated)))
            for _ in range(num_mutations):
                idx = random.randint(0, len(mutated) - 1)
                mutated[idx] = random.choice(crash_triggers)
            data_zone = bytes(mutated)

        # FIX: Protocol/Format Pinning (Combine static required path with the mutated target block)
        final_payload = prefix + data_zone

        # Profile Execution Delivery
        if self.profile.transparent:
            return final_payload
            
        encrypted = bytearray(b ^ self.profile.xor_key for b in final_payload)
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
            # FIX: Captures process termination/dropped frames cleanly without throwing an internal engine exception
            return {"status": "network_error", "reason": str(e)}
        finally:
            if sock is not None:
                sock.close()