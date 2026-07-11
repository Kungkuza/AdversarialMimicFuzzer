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
        fuzzer_status["last_result"] = "Initializing campaign layers..."
        fuzzer_status["crashes"] = []

    # Map selected options to clear data contexts
    if profile_name == "Raw-Numeric":
        profile = FuzzerCore.AdversaryProfile(name="Raw-Numeric", transparent=True)
        target_type, prefix = "numeric_string", b""
    elif profile_name == "Raw-Overflow":
        profile = FuzzerCore.AdversaryProfile(name="Raw-Overflow", transparent=True)
        target_type, prefix = "binary", b""
    elif profile_name == "APT41":
        profile = FuzzerCore.AdversaryProfile(name="APT41", magic_bytes=b"\x4d\x5a", xor_key=0xAA, transparent=False)
        target_type, prefix = "binary", b""
    else:
        profile = FuzzerCore.AdversaryProfile(name="Standard", magic_bytes=b"\x4d\x5a", xor_key=0x55, transparent=False)
        target_type, prefix = "binary", b""

    engine = FuzzerCore.CoreEngine(agent_ip, agent_port, profile)
    base_seed = b"A"

    for i in range(iterations):
        if not fuzzer_status["running"]: 
            break

        # Pass target constraints directly down to the fuzzer execution block
        payload = engine.mutate_and_style(base_seed, prefix=prefix, target_type=target_type)
        result = engine.send_to_agent(payload)

        with status_lock:
            fuzzer_status["payloads_sent"] += 1
            
            if result.get("status") == "success":
                fuzzer_status["last_result"] = f"Round #{i+1}: Sent {len(payload)} bytes. Target processed cleanly."
                
            elif result.get("status") == "crash" or (result.get("status") == "network_error" and "Expecting value" in result.get("reason", "")):
                reason = result.get("reason", "Segmentation Fault / Application Terminated Abruptly")
                stderr = result.get("stderr", "Process exited due to unhandled hardware signal (SIGSEGV/SIGFPE)").strip()
                
                fuzzer_status["last_result"] = f"[!] CRASH logged on iteration {i+1}."
                fuzzer_status["crashes"].append({
                    "iteration": i + 1,
                    "reason": f"Target Fault Verified ({len(payload)} bytes)",
                    "payload_hex": payload.hex()[:40] + "...",
                    "stderr": stderr
                })
                fuzzer_status["running"] = False
                break

            elif result.get("status") == "network_error":
                fuzzer_status["last_result"] = f"Network connection dropped: {result.get('reason')}"
                fuzzer_status["running"] = False
                break

        time.sleep(0.005)

    with status_lock:
        fuzzer_status["running"] = False

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
            <input type="text" name="agent_ip" value="127.0.0.1" required>
            
            <label>Target Agent Port:</label>
            <input type="text" name="agent_port" value="9999" required>
            
            <label>Optimization Target Profile:</label>
            <select name="profile">
                <option value="Raw-Numeric">Raw-Numeric (Optimized for div-zero math logs)</option>
                <option value="Raw-Overflow">Raw-Overflow (Optimized for buffer memory logs)</option>
                <option value="Standard">Standard-Mimic (0x55 Obfuscated Protocol)</option>
                <option value="APT41">APT41-Mimic (0xAA Obfuscated Protocol)</option>
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
                <h4 class="crash">⚠️ Verified Faults / Anomalies Captured:</h4>
                <ul style="padding-left: 20px;">
                {% for crash in status.crashes %}
                    <li style="margin-bottom: 10px;">
                        <strong>[Iteration {{ crash.iteration }}]</strong> - {{ crash.reason }} <br>
                        <small style="color: #bbb;">Telemetry Frame (hex): <code>{{ crash.payload_hex }}</code></small>
                        {% if crash.stderr %}
                            <div class="log-box">{{ crash.stderr }}</div>
                        {% endif %}
                    </li>
                {% endfor %}
                </ul>
            {% endif %}
        </div>
        <br>
        <button onclick="window.location.reload();" style="background:#555;">🔄 Refresh Telemetry Status</button>
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
        return "Campaign actively processing already.", 400
        
    agent_ip = request.form.get('agent_ip')
    agent_port = int(request.form.get('agent_port'))
    profile = request.form.get('profile')
    iterations = int(request.form.get('iterations'))
    
    threading.Thread(target=run_fuzzing_loop, args=(agent_ip, agent_port, profile, iterations), daemon=True).start()
    return render_template_string('<script>alert("Campaign launched successfully!"); window.location.href="/";</script>')

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)