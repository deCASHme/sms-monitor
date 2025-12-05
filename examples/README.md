# Beispiele

Dieser Ordner enthält Beispiele für die Verwendung des SMS Monitors.

## config.json

Beispiel-Konfigurationsdatei mit allen verfügbaren Optionen.

```bash
# Kopieren nach /etc/sms-monitor/
sudo cp config.json /etc/sms-monitor/

# Anpassen
sudo nano /etc/sms-monitor/config.json
```

## webhook_example.py

Einfacher Webhook-Server, der SMS-Benachrichtigungen empfängt.

### Installation

```bash
pip install flask
```

### Verwendung

```bash
# Server starten
python3 webhook_example.py

# In config.json hinzufügen:
# "webhooks": ["http://localhost:5000/webhook/sms"]
```

### Erweiterte Webhook-Beispiele

#### Telegram-Bot

```python
import requests

TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID"

def send_telegram(sms_data):
    message = f"📱 SMS von {sms_data['from']}\n\n{sms_data['text']}"
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, json={
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message
    })
```

#### E-Mail-Benachrichtigung

```python
import smtplib
from email.message import EmailMessage

def send_email(sms_data):
    msg = EmailMessage()
    msg['Subject'] = f"SMS von {sms_data['from']}"
    msg['From'] = 'sms-monitor@example.com'
    msg['To'] = 'your@email.com'
    msg.set_content(sms_data['text'])

    with smtplib.SMTP('localhost') as s:
        s.send_message(msg)
```

#### Discord Webhook

```python
import requests

DISCORD_WEBHOOK_URL = "YOUR_DISCORD_WEBHOOK_URL"

def send_discord(sms_data):
    requests.post(DISCORD_WEBHOOK_URL, json={
        'content': f"📱 SMS von **{sms_data['from']}**",
        'embeds': [{
            'description': sms_data['text'],
            'timestamp': sms_data['timestamp']
        }]
    })
```

## Python-API Beispiel

```python
from sms_monitor import SMSMonitor, Config

# Konfiguration laden
config = Config('/etc/sms-monitor/config.json')

# Monitor erstellen
monitor = SMSMonitor(config)

# Verbindung zum Modem herstellen
if monitor.connect_modem():
    # Einmalig SMS prüfen
    monitor.process_sms()

    # Oder: Kontinuierlich laufen lassen
    # monitor.run()
```

## Systemd Timer (Alternative zum Service)

Falls Sie SMS nur zu bestimmten Zeiten prüfen möchten:

```bash
# /etc/systemd/system/sms-monitor.timer
[Unit]
Description=SMS Monitor Timer

[Timer]
OnCalendar=*:0/5  # Alle 5 Minuten
Persistent=true

[Install]
WantedBy=timers.target
```

```bash
# Timer aktivieren
sudo systemctl enable sms-monitor.timer
sudo systemctl start sms-monitor.timer
```
