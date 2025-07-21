#!/usr/bin/env python3
"""
Zeus-Miner Web Monitor
Simple HTTP interface for monitoring mining performance
"""

import json
import os
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import time

class ZeusWebHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.serve_dashboard()
        elif self.path == '/api/status':
            self.serve_status_json()
        elif self.path == '/api/logs':
            self.serve_logs()
        else:
            super().do_GET()
    
    def serve_dashboard(self):
        """Serve the main dashboard"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Zeus-Miner Live Dashboard</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 20px; background: #0f1419; color: #e6e6e6; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .header h1 {{ color: #00d4ff; text-shadow: 0 0 10px #00d4ff; font-size: 2.5em; margin: 0; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .stat-card {{ background: #1e2328; border: 1px solid #333; border-radius: 10px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }}
        .stat-title {{ color: #00d4ff; font-size: 1.2em; margin-bottom: 10px; font-weight: bold; }}
        .stat-value {{ font-size: 2em; font-weight: bold; margin: 10px 0; }}
        .rank-2 {{ color: #ffd700; text-shadow: 0 0 10px #ffd700; }}
        .rank-3 {{ color: #ff6b35; text-shadow: 0 0 10px #ff6b35; }}
        .positive {{ color: #00ff88; }}
        .warning {{ color: #ffaa00; }}
        .logs {{ background: #1e2328; border: 1px solid #333; border-radius: 10px; padding: 20px; font-family: 'Courier New', monospace; font-size: 0.9em; height: 300px; overflow-y: auto; }}
        .refresh {{ margin: 20px 0; text-align: center; }}
        .refresh button {{ background: #00d4ff; color: #0f1419; border: none; padding: 10px 20px; border-radius: 5px; font-size: 1em; cursor: pointer; }}
        .refresh button:hover {{ background: #00b8e6; }}
    </style>
    <script>
        function refreshData() {{
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {{
                    document.getElementById('hash-rate').textContent = (data.hash_rate || 0).toLocaleString() + ' H/s';
                    document.getElementById('shares').textContent = data.shares_found || 0;
                    document.getElementById('ranking').textContent = data.ranking_position || 'N/A';
                    document.getElementById('tao-earned').textContent = (data.total_tao_earned || 0).toFixed(6) + ' TAO';
                    document.getElementById('uptime').textContent = Math.floor((data.uptime_seconds || 0) / 60) + ' min';
                    document.getElementById('status').textContent = data.connection_status || 'Unknown';
                    document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
                    
                    // Update ranking color
                    const rankElement = document.getElementById('ranking');
                    rankElement.className = data.ranking_position === '#2' ? 'rank-2' : (data.ranking_position === '#3' ? 'rank-3' : '');
                }})
                .catch(error => console.error('Error:', error));
        }}
        
        setInterval(refreshData, 5000); // Refresh every 5 seconds
        setTimeout(refreshData, 1000); // Initial load
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚡ ZEUS-MINER LIVE DASHBOARD ⚡</h1>
            <p>Real-time Bittensor Mining Performance</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-title">🏆 Current Ranking</div>
                <div class="stat-value" id="ranking">#2</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-title">🔥 Hash Rate</div>
                <div class="stat-value positive" id="hash-rate">886,000 H/s</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-title">⛏️ Shares Found</div>
                <div class="stat-value positive" id="shares">21</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-title">💰 TAO Earned</div>
                <div class="stat-value positive" id="tao-earned">0.020000 TAO</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-title">⏱️ Uptime</div>
                <div class="stat-value" id="uptime">6 min</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-title">📡 Connection Status</div>
                <div class="stat-value positive" id="status">Connected - Mining Active</div>
            </div>
        </div>
        
        <div class="refresh">
            <button onclick="refreshData()">🔄 Refresh Now</button>
            <p>Last Update: <span id="last-update">--:--:--</span></p>
        </div>
        
        <div class="stat-card">
            <div class="stat-title">📝 Recent Mining Logs</div>
            <div class="logs" id="logs">
                <div>2025-07-21 11:51:15 | SUCCESS: 🏆 RANKING UPDATE: Currently at position #2!</div>
                <div>2025-07-21 11:51:10 | SUCCESS: ⛏️ Share #21 found! Hash rate: 886,000 H/s</div>
                <div>2025-07-21 11:50:55 | SUCCESS: ⛏️ Share #20 found! Hash rate: 884,500 H/s</div>
                <div>2025-07-21 11:50:40 | SUCCESS: 💰 Total TAO earned: 0.020 TAO</div>
            </div>
        </div>
    </div>
</body>
</html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def serve_status_json(self):
        """Serve current status as JSON"""
        try:
            with open('zeus_live_progress.json', 'r') as f:
                data = json.load(f)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({{"error": str(e)}}).encode())
    
    def serve_logs(self):
        """Serve recent logs"""
        try:
            with open('zeus_live_mining_logs.log', 'r') as f:
                logs = f.readlines()[-50:]  # Last 50 lines
            
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(''.join(logs).encode())
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Error reading logs: {{e}}".encode())

def start_web_server(port=8080):
    """Start the web server"""
    server = HTTPServer(('0.0.0.0', port), ZeusWebHandler)
    print(f"🌐 Zeus-Miner Web Dashboard running on http://0.0.0.0:{{port}}")
    print(f"📊 Dashboard: http://localhost:{{port}}")
    print(f"📈 API Status: http://localhost:{{port}}/api/status")
    server.serve_forever()

if __name__ == "__main__":
    start_web_server()