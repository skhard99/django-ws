#!/usr/bin/env python3
"""
Simple webhook server to receive Prometheus alerts for testing
"""
from flask import Flask, request, jsonify
import json
from datetime import datetime

app = Flask(__name__)

@app.route('/alerts', methods=['POST'])
def receive_alert():
    """Receive and log Prometheus alerts"""
    try:
        data = request.get_json()
        
        print(f"\n{'='*50}")
        print(f"[{datetime.now()}] ALERT RECEIVED")
        print(f"{'='*50}")
        
        if data and 'alerts' in data:
            for alert in data['alerts']:
                status = alert.get('status', 'unknown')
                alert_name = alert.get('labels', {}).get('alertname', 'unknown')
                deployment_color = alert.get('labels', {}).get('deployment_color', 'unknown')
                severity = alert.get('labels', {}).get('severity', 'unknown')
                
                print(f"🚨 ALERT: {alert_name}")
                print(f"📊 Status: {status}")
                print(f"🎯 Deployment: {deployment_color}")
                print(f"⚠️  Severity: {severity}")
                
                if 'annotations' in alert:
                    summary = alert['annotations'].get('summary', 'No summary')
                    description = alert['annotations'].get('description', 'No description')
                    print(f"📝 Summary: {summary}")
                    print(f"📋 Description: {description}")
                
                print(f"⏰ Starts at: {alert.get('startsAt', 'unknown')}")
                if status == 'resolved':
                    print(f"✅ Resolved at: {alert.get('endsAt', 'unknown')}")
                print("-" * 50)
        
        print(f"Full payload:")
        print(json.dumps(data, indent=2))
        print(f"{'='*50}\n")
        
        return jsonify({"status": "received", "timestamp": datetime.now().isoformat()})
    
    except Exception as e:
        print(f"Error processing alert: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "webhook-server",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/', methods=['GET'])
def home():
    """Home page"""
    return """
    <h1>Prometheus Alert Webhook Server</h1>
    <p>This server receives and logs Prometheus alerts.</p>
    <p>Endpoints:</p>
    <ul>
        <li><code>POST /alerts</code> - Receive alerts</li>
        <li><code>GET /health</code> - Health check</li>
    </ul>
    <p>Check the container logs to see received alerts.</p>
    """

if __name__ == '__main__':
    print("🚀 Starting Prometheus Alert Webhook Server on port 5001")
    print("📡 Listening for alerts at http://0.0.0.0:5001/alerts")
    app.run(host='0.0.0.0', port=5001, debug=True)