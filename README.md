# SMS Monitor für USB 4G/LTE Modems

Ein einfaches Python-Tool zum Empfangen und Verwalten von SMS über USB 4G/LTE Modems unter Linux mit ModemManager.

## Features

- ✅ Automatischer SMS-Empfang im Hintergrund
- ✅ Speicherung von SMS als Textdateien
- ✅ Webhook-Benachrichtigungen bei neuen SMS
- ✅ Duplikaterkennung
- ✅ CLI-Tool für manuelle Verwaltung
- ✅ Systemd-Integration für automatischen Start
- ✅ Unterstützt alle ModemManager-kompatiblen USB-Modems
- ✅ Einfache Installation und Konfiguration

## Getestete Hardware

- SIMCOM SIM7600G-H (USB ID: 1e0e:9001)
- Weitere ModemManager-kompatible USB-Modems

## Voraussetzungen

- Linux-System (Debian, Ubuntu, etc.)
- Python 3.7 oder höher
- ModemManager installiert und aktiv
- USB 4G/LTE Modem mit SIM-Karte

## Schnellstart

### 1. System vorbereiten

```bash
# ModemManager installieren
sudo apt update
sudo apt install modemmanager python3-pip python3-gi gir1.2-modemmanager-1.0

# ModemManager starten
sudo systemctl start ModemManager
sudo systemctl enable ModemManager

# Modem prüfen
mmcli -L
mmcli -m 0  # Falls Modem mit SIM-PIN gesperrt: mmcli -i 0 --pin=XXXX
```

### 2. SMS Monitor installieren

```bash
# Repository klonen
git clone https://github.com/deCASHme/sms-monitor.git
cd sms-monitor

# Installation ausführen
sudo ./install.sh
```

### 3. Konfigurieren

```bash
# Beispiel-Konfiguration erstellen
sudo mkdir -p /etc/sms-monitor
sudo sms-monitor config --create-example /etc/sms-monitor/config.json

# Konfiguration anpassen (optional)
sudo nano /etc/sms-monitor/config.json
```

### 4. Service starten

```bash
# Service aktivieren und starten
sudo systemctl enable sms-monitor
sudo systemctl start sms-monitor

# Status prüfen
sudo systemctl status sms-monitor

# Logs ansehen
sudo journalctl -u sms-monitor -f
```

## Verwendung

### Als Service (empfohlen)

Der SMS-Monitor läuft im Hintergrund und prüft automatisch auf neue SMS:

```bash
# Service starten
sudo systemctl start sms-monitor

# Service stoppen
sudo systemctl stop sms-monitor

# Status prüfen
sudo systemctl status sms-monitor

# Logs ansehen
sudo journalctl -u sms-monitor -f
```

### CLI-Tool

Für manuelle Operationen steht das `sms-monitor` Kommando zur Verfügung:

```bash
# Einmalig auf SMS prüfen
sms-monitor check

# Alle gespeicherten SMS anzeigen
sms-monitor list

# SMS mit vollständigem Inhalt anzeigen
sms-monitor list --verbose

# Statistiken anzeigen
sms-monitor stats

# Modem-Informationen anzeigen
sms-monitor modem-info

# Konfiguration anzeigen
sms-monitor config --show

# Hilfe anzeigen
sms-monitor --help
```

### Als Python-Modul

```python
from sms_monitor import SMSMonitor, Config

# Konfiguration laden
config = Config('/etc/sms-monitor/config.json')

# Monitor erstellen und starten
monitor = SMSMonitor(config)
monitor.run()
```

## Konfiguration

Die Konfigurationsdatei liegt standardmäßig unter `/etc/sms-monitor/config.json`:

```json
{
  "modem_index": 0,
  "sms_dir": "/var/spool/sms",
  "log_file": "/var/log/sms-monitor.log",
  "log_level": "INFO",
  "processed_db": "/var/lib/sms-monitor/processed.json",
  "check_interval": 30,
  "delete_after_read": true,
  "webhooks": [],
  "enable_console_output": true
}
```

### Konfigurationsoptionen

| Option | Typ | Beschreibung | Standard |
|--------|-----|--------------|----------|
| `modem_index` | int | Index des zu verwendenden Modems (bei mehreren Modems) | `0` |
| `sms_dir` | string | Verzeichnis für gespeicherte SMS | `/var/spool/sms` |
| `log_file` | string | Pfad zur Log-Datei | `/var/log/sms-monitor.log` |
| `log_level` | string | Log-Level: DEBUG, INFO, WARNING, ERROR | `INFO` |
| `processed_db` | string | Datenbank für verarbeitete SMS | `/var/lib/sms-monitor/processed.json` |
| `check_interval` | int | Prüf-Intervall in Sekunden | `30` |
| `delete_after_read` | bool | SMS nach dem Lesen vom Modem löschen | `true` |
| `webhooks` | array | Liste von Webhook-URLs für Benachrichtigungen | `[]` |
| `enable_console_output` | bool | Ausgabe auch in Konsole | `true` |

## Webhook-Benachrichtigungen

Der SMS-Monitor kann bei eingehenden SMS Webhooks aufrufen:

```json
{
  "webhooks": [
    "https://example.com/webhook/sms",
    "https://your-server.com/api/notify"
  ]
}
```

Payload-Format:

```json
{
  "from": "+4912345678",
  "text": "SMS-Nachricht",
  "timestamp": "2025-12-05T01:42:23+02:00",
  "received_at": "2025-12-05T01:42:30.123456"
}
```

Webhook-Beispiel siehe: [examples/webhook_example.py](examples/webhook_example.py)

## Gespeicherte SMS

SMS werden als Textdateien gespeichert unter `/var/spool/sms/`:

```
20251205_014223_4912345678.txt
```

Inhalt:

```
Von: +4912345678
Zeit: 2025-12-05T01:42:23+02:00
Status: MM_SMS_STATE_RECEIVED

Nachricht:
Dies ist eine Test-SMS.
```

## Troubleshooting

### Modem wird nicht erkannt

```bash
# USB-Geräte prüfen
lsusb

# Kernel-Meldungen prüfen
dmesg | grep -i "usb\|tty" | tail -20

# ModemManager neu starten
sudo systemctl restart ModemManager
sleep 3
mmcli -L
```

### Modem ist gesperrt (SIM-PIN)

```bash
# PIN eingeben
mmcli -i 0 --pin=1234

# Status prüfen
mmcli -m 0
```

### Keine ttyUSB-Geräte

```bash
# USB-Treiber laden
sudo modprobe option
sudo modprobe qcserial

# Vendor/Product ID zuweisen (Beispiel für SimTech)
echo "1e0e 9001" | sudo tee /sys/bus/usb-serial/drivers/option1/new_id
```

### Service startet nicht

```bash
# Logs prüfen
sudo journalctl -u sms-monitor -n 50

# Manuell testen
sudo /usr/local/bin/sms-monitor run

# Konfiguration prüfen
sms-monitor config --show
```

## Deinstallation

```bash
# Service stoppen und deaktivieren
sudo systemctl stop sms-monitor
sudo systemctl disable sms-monitor

# Dateien entfernen
sudo rm /usr/local/bin/sms-monitor
sudo rm /etc/systemd/system/sms-monitor.service
sudo rm -rf /usr/local/lib/sms-monitor
sudo rm -rf /etc/sms-monitor

# Optional: Gespeicherte SMS und Logs behalten oder löschen
sudo rm -rf /var/spool/sms
sudo rm -rf /var/lib/sms-monitor
sudo rm /var/log/sms-monitor.log

# Systemd neu laden
sudo systemctl daemon-reload
```

## Projektstruktur

```
opt/
├── sms_monitor/
│   ├── __init__.py       # Paket-Initialisierung
│   ├── config.py         # Konfigurationsverwaltung
│   ├── monitor.py        # Hauptmodul (SMS-Empfang)
│   └── cli.py            # CLI-Tool
├── examples/
│   ├── config.json       # Beispiel-Konfiguration
│   └── webhook_example.py # Webhook-Server Beispiel
├── systemd/
│   └── sms-monitor.service # Systemd Service
├── install.sh            # Installations-Script
├── requirements.txt      # Python-Abhängigkeiten
├── setup.py              # Python-Setup
├── README.md             # Diese Datei
└── LICENSE               # MIT-Lizenz
```

## Entwicklung

```bash
# Development-Installation
git clone https://github.com/deCASHme/sms-monitor.git
cd sms-monitor

# Virtual Environment erstellen
python3 -m venv venv
source venv/bin/activate

# Abhängigkeiten installieren
pip install -r requirements.txt

# Entwicklungsmodus installieren
pip install -e .

# Tests ausführen (wenn vorhanden)
python -m pytest
```

## Beitragen

Contributions sind willkommen! Bitte:

1. Forke das Repository
2. Erstelle einen Feature-Branch (`git checkout -b feature/AmazingFeature`)
3. Committe deine Änderungen (`git commit -m 'Add some AmazingFeature'`)
4. Push zum Branch (`git push origin feature/AmazingFeature`)
5. Öffne einen Pull Request

## Lizenz

Dieses Projekt ist lizenziert unter der MIT-Lizenz - siehe [LICENSE](LICENSE) Datei für Details.

## Autor

**deCASHme** - [https://github.com/deCASHme](https://github.com/deCASHme)

## Danksagungen

- ModemManager Team
- Python GObject Introspection
- Linux Kernel USB-Serial Entwickler

## Support

Bei Fragen oder Problemen:

- GitHub Issues: [https://github.com/deCASHme/sms-monitor/issues](https://github.com/deCASHme/sms-monitor/issues)
- Dokumentation: [https://github.com/deCASHme/sms-monitor](https://github.com/deCASHme/sms-monitor)

## Changelog

### Version 1.0.0 (2025-12-05)

- Initiale Version
- SMS-Empfang über ModemManager
- CLI-Tool
- Systemd-Integration
- Webhook-Unterstützung
- Duplikaterkennung
