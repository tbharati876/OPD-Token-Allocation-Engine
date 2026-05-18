# 1. Install Libraries
!pip install flask pyngrok pytz -q

import os
import heapq
from datetime import datetime
import pytz
from flask import Flask, render_template_string, request, jsonify
from pyngrok import ngrok

# 2. BACKEND Engine
class TokenEngine:
    def __init__(self):
        self.PRIORITY_MAP = {"EMERGENCY": 0, "PAID": 1, "FOLLOW_UP": 2, "ONLINE": 3, "WALK_IN": 4}
        self.capacity = 5
        self.IST = pytz.timezone('Asia/Kolkata')
        self.doctors = {
            "Dr. Smith": {"09:00-10:00": [], "10:00-11:00": []},
            "Dr. Jones": {"09:00-10:00": [], "10:00-11:00": []},
            "Dr. Taylor": {"09:00-10:00": [], "10:00-11:00": []}
        }

    def get_ist_time(self):
        return datetime.now(self.IST)

    def add_patient(self, doctor, slot, name, category):
        if doctor not in self.doctors or slot not in self.doctors[doctor]:
            return False, "Invalid Doctor/Slot"

        queue = self.doctors[doctor][slot]

        if len(queue) >= self.capacity and category != "EMERGENCY":
            return False, f"Slot Full! (Capacity: {self.capacity})"

        priority = self.PRIORITY_MAP.get(category, 5)
        now_ist = self.get_ist_time()

        token = {
            "name": name,
            "category": category,
            "time": now_ist.strftime("%I:%M:%S %p") # 12-hour format with AM/PM
        }

        heapq.heappush(queue, (priority, now_ist, token))
        return True, token

    def get_queue(self, doctor, slot):
        # Returns sorted list based on priority, then time
        return [item[2] for item in sorted(self.doctors[doctor][slot])]

engine = TokenEngine()
app = Flask(__name__)

# 3. FRONTEND  Web UI To get App
HTML_UI = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>OPD Token Allocation Engine</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #f4f7f6; font-family: 'Segoe UI', sans-serif; }
        .emergency-row { background-color: #fff0f0 !important; border-left: 5px solid #d90429; }
        .card { border-radius: 15px; border: none; box-shadow: 0 10px 20px rgba(0,0,0,0.05); }
        .navbar { background: #003049; }
        .badge-EMERGENCY { background-color: #d90429; }
        .badge-PAID { background-color: #f77f00; }
        .badge-WALK_IN { background-color: #6c757d; }
    </style>
</head>
<body>
<nav class="navbar navbar-dark mb-4">
    <div class="container text-white">
        <span class="navbar-brand mb-0 h1">🏥OPD  Token Allocation Engine</span>
    </div>
</nav>

<div class="container">
    <div class="row g-4">
        <div class="col-md-4">
            <div class="card p-4">
                <h5 class="mb-3">Patient Registration</h5>
                <form id="bookingForm">
                    <label class="small text-muted">Doctor</label>
                    <select id="doctor" class="form-select mb-2" onchange="updateView()">
                        <option>Dr. Smith</option><option>Dr. Jones</option><option>Dr. Taylor</option>
                    </select>

                    <label class="small text-muted">Slot</label>
                    <select id="slot" class="form-select mb-2" onchange="updateView()">
                        <option>09:00-10:00</option><option>10:00-11:00</option>
                    </select>

                    <label class="small text-muted">Patient Name</label>
                    <input type="text" id="p_name" class="form-control mb-2" placeholder="e.g. Rajesh Kumar" required>

                    <label class="small text-muted">Category</label>
                    <select id="category" class="form-select mb-4">
                        <option value="WALK_IN">Walk-In</option>
                        <option value="ONLINE">Online Booking</option>
                        <option value="FOLLOW_UP">Follow-Up</option>
                        <option value="PAID">Paid Priority</option>
                        <option value="EMERGENCY">EMERGENCY</option>
                    </select>

                    <button type="submit" class="btn btn-primary w-100">Issue Token</button>
                </form>
            </div>
        </div>

        <div class="col-md-8">
            <div class="card p-4">
                <div class="d-flex justify-content-between">
                    <h5>Priority Queue</h5>
                    <div id="liveTime" class="text-primary fw-bold"></div>
                </div>
                <hr>
                <table class="table align-middle mt-2">
                    <thead>
                        <tr class="text-muted">
                            <th>Pos</th><th>Patient Name</th><th>Category</th><th>Booking Time</th>
                        </tr>
                    </thead>
                    <tbody id="queueBody"></tbody>
                </table>
                <div id="emptyMsg" class="text-center py-5 text-muted">Queue is currently empty.</div>
            </div>
        </div>
    </div>
</div>

<script>
    function updateLiveClock() {
        const now = new Date().toLocaleString("en-US", {timeZone: "Asia/Kolkata", hour: '2-digit', minute:'2-digit', second:'2-digit'});
        document.getElementById('liveTime').innerText = "Time: " + now;
    }
    setInterval(updateLiveClock, 1000);

    async function updateView() {
        const doc = document.getElementById('doctor').value;
        const slot = document.getElementById('slot').value;
        const res = await fetch(`/api/queue?doctor=${doc}&slot=${slot}`);
        const data = await res.json();

        const body = document.getElementById('queueBody');
        const msg = document.getElementById('emptyMsg');

        body.innerHTML = '';
        if (data.length === 0) { msg.style.display = 'block'; return; }

        msg.style.display = 'none';
        data.forEach((p, i) => {
            const row = `<tr class="${p.category === 'EMERGENCY' ? 'emergency-row' : ''}">
                <td>#${i+1}</td>
                <td>${p.name}</td>
                <td><span class="badge badge-${p.category} bg-secondary">${p.category}</span></td>
                <td>${p.time}</td>
            </tr>`;
            body.innerHTML += row;
        });
    }

    document.getElementById('bookingForm').onsubmit = async (e) => {
        e.preventDefault();
        const payload = {
            doctor: document.getElementById('doctor').value,
            slot: document.getElementById('slot').value,
            name: document.getElementById('p_name').value,
            category: document.getElementById('category').value
        };

        const res = await fetch('/api/book', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });

        const result = await res.json();
        if(result.status === 'success') {
            document.getElementById('p_name').value = '';
            updateView();
        } else {
            alert(result.message);
        }
    };
    window.onload = updateView;
</script>
</body>
</html>
"""

# 4. API
@app.route('/')
def home():
    return render_template_string(HTML_UI)

@app.route('/api/book', methods=['POST'])
def book_api():
    data = request.json
    success, resp = engine.add_patient(data['doctor'], data['slot'], data['name'], data['category'])
    return jsonify({"status": "success" if success else "error", "message": resp})

@app.route('/api/queue')
def queue_api():
    doctor = request.args.get('doctor')
    slot = request.args.get('slot')
    return jsonify(engine.get_queue(doctor, slot))

# 5. Setting of NGROK Token and Server
NGROK_TOKEN = "PASTE_NGROK_TOKEN_HERE"
ngrok.set_auth_token(NGROK_TOKEN)

try:
    public_url = ngrok.connect(5000).public_url
    print(f"OPD Token Allocation Engine APP: {public_url}")
except Exception as e:
    print(f"Ngrok Error: {e}")

app.run(port=5000)
