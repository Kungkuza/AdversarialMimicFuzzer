from flask import Flask, request, jsonify, render_template_string
from FuzzerCore import CoreEngine, AdversaryProfile
import threading
import FuzzerCore
import time

app = Flask(__name__)

# Global state to keep track of the current fuzzing campaign status
fuzzer_status = {
    "running": False,
    "payloads_sent": 0,
    "last_result": "No campaign started yet.",
    "crashes": []
}

def run_fuzzing_loop(agent_ip, agent_port, profile_name, iterations):
    global fuzzer_status
    fuzzer_status["running"] = True
    fuzzer_status["total_sent"] = 0
    fuzzer_status["crashes"] = 0

    print(f"[*] Kicking off background campaign against {agent_ip}:{agent_port}")

    profile = FuzzerCore.AdversaryProfile(name=profile_name)
    engine = FuzzerCore.CoreEngine(agent_ip, agent_port, profile)

    base_seed = b"A" * 20 

    for i in range(iterations):
        if not fuzzer_status["running"]: # Allow stopping campaigns
            break

        # Generate a mutated, styled payload
        payload = engine.mutate_and_style(base_seed)

        # Send it across the network to the Ubuntu Agent
        result = engine.send_to_agent(payload)

        # Track results and update stats for your Web UI dashboard
        fuzzer_status["total_sent"] += 1
        
        if result.get("status") == "crash":
            fuzzer_status["crashes"] += 1
            print(f"[!] Crash found on iteration {i}! Payload: {payload.hex()}")
        elif result.get("status") == "network_error":
            print(f"[!!!] Network connection failed: {result.get('reason')}")
            fuzzer_status["running"] = False
            break

        # Tiny sleep so you don't instantly melt the socket buffers
        time.sleep(0.01)

    fuzzer_status["running"] = False
    print("[*] Fuzzing campaign completed.")

# HTML Dashboard Template directly embedded for simplicity
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
            
            <label>Adversary Profile Style:</label>
            <select name="profile">
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
                <ul>
                {% for crash in status.crashes %}
                    <li>[Iter {{ crash.iteration }}] - {{ crash.reason }} (Payload: <code>{{ crash.payload_hex }}</code>)</li>
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
    
    threading.Thread(target=run_fuzzing_loop, args=(agent_ip, agent_port, profile, iterations)).start()
    
    return render_template_string('<script>alert("Campaign started successfully!"); window.location.href="/";</script>')

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)