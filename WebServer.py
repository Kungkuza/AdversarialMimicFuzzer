from flask import Flask, request, jsonify, render_template_string
from FuzzerCore import CoreEngine, AdversaryProfile
import threading
import FuzzerCore
import time

app = Flask(__name__)

fuzzer_status = {
    "running": False,
    "payloads_sent": 0,
    "last_result": "No campaign started yet.",
    "crashes": []
}

status_lock = threading.Lock()

def run_fuzzing_loop(agent_ip, agent_port, profile_name, iterations):
    global fuzzer_status
    
    with status_lock:
        fuzzer_status["running"] = True
        fuzzer_status["payloads_sent"] = 0
        fuzzer_status["last_result"] = "Initializing adversary campaign engine..."
        fuzzer_status["crashes"] = []

    print(f"[*] Kicking off background campaign against {agent_ip}:{agent_port}")
    print("="*60 + "\n")

    if profile_name == "Raw-Testing":
        profile = FuzzerCore.AdversaryProfile(name="Raw-Testing", transparent=True)
    elif profile_name == "APT41":
        profile = FuzzerCore.AdversaryProfile(name="APT41", magic_bytes=b"\x4d\x5a", xor_key=0xAA, transparent=False)
    else:
        profile = FuzzerCore.AdversaryProfile(name="Standard", magic_bytes=b"\x4d\x5a", xor_key=0x55, transparent=False)

    engine = FuzzerCore.CoreEngine(agent_ip, agent_port, profile)
    base_seed = b"A" * 64

    for i in range(iterations):
        if not fuzzer_status["running"]: 
            print("[-] Campaign aborted by user request.")
            break

        payload = engine.mutate_and_style(base_seed)
        result = engine.send_to_agent(payload)

        with status_lock:
            fuzzer_status["payloads_sent"] += 1
            
            if result.get("status") == "success":
                fuzzer_status["last_result"] = f"Round #{i+1}: Sent {len(payload)} bytes. Target processed cleanly."
                
            elif result.get("status") == "crash" or (result.get("status") == "network_error" and "Expecting value" in result.get("reason", "")):
                reason = "Segmentation Fault (Dropped Connection / Empty JSON Response)"
                if result.get("status") == "crash":
                    reason = result.get("reason", "Segmentation Fault / Core Dump")
                
                stderr = result.get("stderr", "Process terminated abnormally (SIGSEGV)").strip()
                fuzzer_status["last_result"] = f"[!] CRASH found on iteration {i+1}: {reason}"
                
                fuzzer_status["crashes"].append({
                    "iteration": i + 1,
                    "reason": f"Target Disturbance Verified ({len(payload)} bytes payload)",
                    "payload_hex": payload.hex()[:40] + "...",
                    "stderr": stderr
                })
                
                print("\n" + "!"*60)
                print(f"[!] TARGET BINARY CRASHED ON ITERATION #{i+1}!")
                print(f"    -> Payload Size: {len(payload)} bytes")
                print(f"    -> Agent Reason: {reason}")
                print(f"    -> Faulting Payload (hex): {payload.hex()}")
                print("!"*60 + "\n")
                fuzzer_status["running"] = False
                break

            elif result.get("status") == "network_error":
                err_msg = f"Network connection failed: {result.get('reason')}"
                print(f"[!!!] {err_msg}")
                fuzzer_status["last_result"] = f"[!!!] {err_msg}"
                fuzzer_status["running"] = False
                break

        time.sleep(0.01)

    with status_lock:
        fuzzer_status["running"] = False
    print("[*] Fuzzing campaign completed.")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Adversary Mimic Fuzzer Panel</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 30px; background: #1e1e1e; color: #fff; }
        .container { max-width: 800px; margin: auto; background: #2d2d2d; padding: 20px; border-radius: 8px; }
        input, select, button { padding: 10px; margin: 5px 0; width: 100%; box-sizing: border-box; }
        button { background: #007acc; color: white; border: none; cursor: pointer; font-weight: bold;}
        .status-box { background: #3c3c3c; padding: 15px; margin-top: 20px; border-left: 5px solid #007acc; }
        .crash { color: #ff5555; font-weight: bold; }
        .log-box { font-family: monospace; font-size: 12px; background: #111; padding: 10px; border-radius: 4px; overflow-x: auto; white-space: pre-wrap; margin: 5px 0; color: #ff5555;}
    </style>
</head>
<body>
    <div class="container">
        <h2>⚔️ Adversary Mimic Fuzzer Orchestrator</h2>
        <form action="/start" method="post">
            <label>Target Agent IP:</label>
            <input type="text" name="agent_ip" value="192.168.56.102" required>
            
            <label>Target Agent Port:</label>
            <input type="text" name="agent_port" value="9999" required>
            
            <label>Adversary Profile Style:</label>
            <select name="profile">
                <option value="Raw-Testing">Raw-Testing (Transparent Direct Mutations)</option>
                <option value="Standard">Standard-Mimic (NOP Sleds + 0x55 XOR)</option>
                <option value="APT41">APT41 Mimic (PE Headers + 0xAA XOR)</option>
            </select>
            
            <label>Iterations:</label>
            <input type="number" name="iterations" value="1000">
            
            <button type="submit">🚀 Launch Campaign</button>
        </form>

        <div class="status-box">
            <h3>Campaign Monitor</h3>
            <p><strong>Status:</strong> {{ 'RUNNING ⏳' if status.running else 'IDLE 🛑' }}</p>
            <p><strong>Payloads Dispatched:</strong> {{ status.payloads_sent }}</p>
            <p><strong>Latest Agent Output:</strong> {{ status.last_result }}</p>
            
            {% if status.crashes %}
                <h4 class="crash">⚠️ Detected Crashes / Bypasses:</h4>
                <ul style="padding-left: 20px;">
                {% for crash in status.crashes %}
                    <li style="margin-bottom: 10px;">
                        <strong>[Iter {{ crash.iteration }}]</strong> - {{ crash.reason }} <br>
                        <small style="color: #bbb;">Payload: <code>{{ crash.payload_hex }}</code></small>
                        {% if crash.stderr %}
                            <div class="log-box">{{ crash.stderr }}</div>
                        {% endif %}
                    </li>
                {% endfor %}
                </ul>
            {% endif %}
        </div>
        <br>
        <button onclick="window.location.reload();" style="background:#555;">🔄 Refresh Stats</button>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE, status=fuzzer_status)

@app.route('/start', methods=['POST'])
def start_fuzzer():
    if fuzzer_status["running"]:
        return "A campaign is already running!", 400
        
    agent_ip = request.form.get('agent_ip')
    agent_port = int(request.form.get('agent_port'))
    profile = request.form.get('profile')
    iterations = int(request.form.get('iterations'))
    
    threading.Thread(target=run_fuzzing_loop, args=(agent_ip, agent_port, profile, iterations), daemon=True).start()
    
    return render_template_string('<script>alert("Campaign started successfully!"); window.location.href="/";</script>')

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)