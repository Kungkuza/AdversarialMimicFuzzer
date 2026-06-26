import random
import sys

class AdversaryProfile:
    """Defines the traits of the threat actor we want to mimic."""
    def __init__(self, name):
        self.name = name
        #Mimicking an actor that uses specific magic bytes and XOR obfuscation
        self.magic_bytes = b"\x4d\x5a"  # e.g., PE Header mimicry
        self.xor_key = 0xAA
        self.preferred_padding = b"\x90" # NOP sled mimicry

class MimicFuzzer:
    def __init__(self, profile: AdversaryProfile):
        self.profile = profile

    def mutate_bit_flip(self, data: bytearray) -> bytearray:
        """Standard fuzzing mutation: Flip a random bit."""
        if not data:
            return data
        byte_idx = random.randint(0, len(data) - 1)
        bit_idx = random.randint(0, 7)
        data[byte_idx] ^= (1 << bit_idx)
        return data

    def apply_adversary_style(self, data: bytes) -> bytes:
        """Transforms a mutated payload to look like the adversary's toolkit."""
        mutated = bytearray(data)
        
        #Apply bit flip mutation first
        mutated = self.mutate_bit_flip(mutated)
        
        #Mimic Adversary behavior: XOR encrypt a portion of the payload
        xor_mutated = bytearray(b ^ self.profile.xor_key for b in mutated)
        
        #Mimic Adversary behavior: Prepend magic bytes and add a NOP sled
        final_payload = self.profile.magic_bytes + (self.profile.preferred_padding * 4) + xor_mutated
        return bytes(final_payload)

#TARGET FOR FUZZING
def target_software(payload: bytes):
    """
    Simulates a vulnerable parser. 
    It crashes if it detects the adversary's signature combined with a specific mutation.
    """
    # Let's say the parser handles the adversary's magic bytes, 
    # but has a buffer overflow/logic bug if certain conditions are met deep inside.
    if payload.startswith(b"\x4d\x5a"):
        # Strip header to parse 'data'
        body = payload[6:] 
        
        # Simulating a crash condition (e.g., a specific byte combination after XOR)
        if len(body) > 5 and body[2] == 0x00 and body[4] == 0xFF:
            raise IndexError("CRASH DETECTED: Memory corruption simulated via adversary mimicry!")

#MAIN FUZZING LOOP
def main():
    print("[*] Initializing Adversary Mimic Fuzzer...")
    
    # Setup the APT profile
    apt_profile = AdversaryProfile(name="APT-Mimic-42")
    fuzzer = MimicFuzzer(profile=apt_profile)
    
    # Base seed data to mutate
    seed_data = b"hello_security_target"
    iterations = 10000
    crashes = 0
    
    print(f"[*] Mimicking Profile: {apt_profile.name}")
    print(f"[*] Running {iterations} fuzzing iterations against the target...")

    for i in range(iterations):
        # Generate the styled payload
        payload = fuzzer.apply_adversary_style(seed_data)
        
        try:
            target_software(payload)
        except IndexError as e:
            crashes += 1
            print(f"\n[!] Crash found on iteration {i}!")
            print(f"    Payload (hex): {payload.hex()[:50]}...")
            print(f"    Error: {e}")
            # In a real fuzzer, you'd log this payload to a file for triage
            break
    
    if crashes == 0:
        print("\n[*] Fuzzing complete. No crashes detected.")

if __name__ == "__main__":
    main()