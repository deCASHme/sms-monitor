#!/usr/bin/env python3
"""
Beispiel: Einfacher Webhook-Server für SMS-Benachrichtigungen
==============================================================

Startet einen HTTP-Server, der SMS-Benachrichtigungen empfängt.

Installation:
    pip install flask

Verwendung:
    python3 webhook_example.py

In der Konfiguration (/etc/sms-monitor/config.json) hinzufügen:
    "webhooks": ["http://localhost:5000/webhook/sms"]
"""

from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)


@app.route('/webhook/sms', methods=['POST'])
def receive_sms():
    """SMS-Webhook-Endpunkt"""
    try:
        data = request.get_json()

        print("\n" + "=" * 60)
        print(f"SMS EMPFANGEN: {datetime.now()}")
        print("=" * 60)
        print(f"Von:        {data.get('from')}")
        print(f"Zeit:       {data.get('timestamp')}")
        print(f"Empfangen:  {data.get('received_at')}")
        print(f"Nachricht:  {data.get('text')}")
        print("=" * 60)
        print()

        # Hier können weitere Aktionen durchgeführt werden:
        # - SMS in Datenbank speichern
        # - E-Mail versenden
        # - Push-Benachrichtigung senden
        # - API-Call an andere Services

        return jsonify({
            'status': 'success',
            'message': 'SMS received'
        }), 200

    except Exception as e:
        print(f"Fehler: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health-Check Endpunkt"""
    return jsonify({'status': 'ok'}), 200


if __name__ == '__main__':
    print("Webhook-Server startet...")
    print("Listening auf: http://localhost:5000/webhook/sms")
    print("Health-Check:  http://localhost:5000/health")
    print("\nDrücke Strg+C zum Beenden\n")

    app.run(host='0.0.0.0', port=5000, debug=True)
