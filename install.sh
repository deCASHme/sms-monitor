#!/bin/bash
#
# SMS Monitor Installation Script
# ================================
#
# Installiert den SMS Monitor als System-Service
#

set -e

# Farben für Ausgabe
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}SMS Monitor Installation${NC}"
echo "=========================="
echo ""

# Root-Check
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Fehler: Dieses Script muss als root ausgeführt werden${NC}"
    echo "Bitte mit sudo ausführen: sudo ./install.sh"
    exit 1
fi

# Betriebssystem-Check
if ! command -v apt &> /dev/null; then
    echo -e "${YELLOW}Warnung: apt nicht gefunden. Dieses Script ist für Debian/Ubuntu optimiert.${NC}"
    read -p "Trotzdem fortfahren? (j/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Jj]$ ]]; then
        exit 1
    fi
fi

echo "1. System-Abhängigkeiten installieren..."
apt update
apt install -y python3 python3-pip python3-gi gir1.2-mm-1.0 modemmanager libqmi-utils

echo ""
echo "2. Python-Paket installieren..."
pip3 install --upgrade pip
pip3 install PyGObject requests

# Installation im System
echo ""
echo "3. SMS Monitor installieren..."
pip3 install -e .

# Symlink für einfachen Zugriff (falls pip install nicht funktioniert hat)
if ! command -v sms-monitor &> /dev/null; then
    echo "Erstelle Symlink für sms-monitor..."
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    ln -sf "$SCRIPT_DIR/sms_monitor/cli.py" /usr/local/bin/sms-monitor
    chmod +x /usr/local/bin/sms-monitor
fi

# Konfigurationsverzeichnis erstellen
echo ""
echo "4. Konfiguration erstellen..."
mkdir -p /etc/sms-monitor

if [ ! -f /etc/sms-monitor/config.json ]; then
    cp examples/config.json /etc/sms-monitor/config.json
    echo -e "${GREEN}Konfigurationsdatei erstellt: /etc/sms-monitor/config.json${NC}"
else
    echo -e "${YELLOW}Konfiguration existiert bereits: /etc/sms-monitor/config.json${NC}"
fi

# Verzeichnisse für SMS und Logs erstellen
echo ""
echo "5. Verzeichnisse erstellen..."
mkdir -p /var/spool/sms
mkdir -p /var/lib/sms-monitor
mkdir -p /var/log
touch /var/log/sms-monitor.log

# Systemd Service installieren
echo ""
echo "6. Systemd Service installieren..."
cp systemd/sms-monitor.service /etc/systemd/system/
systemctl daemon-reload

# ModemManager starten
echo ""
echo "7. ModemManager starten..."
systemctl enable ModemManager
systemctl start ModemManager

# Modem-Check
echo ""
echo "8. Modem-Status prüfen..."
sleep 2

if mmcli -L 2>/dev/null | grep -q "Modem"; then
    echo -e "${GREEN}✓ Modem erkannt${NC}"
    mmcli -L

    echo ""
    echo "Modem-Details:"
    mmcli -m 0 2>/dev/null | grep -E "manufacturer|model|state|lock" || true

    if mmcli -m 0 2>/dev/null | grep -q "lock: sim-pin"; then
        echo ""
        echo -e "${YELLOW}⚠ Modem ist mit SIM-PIN gesperrt${NC}"
        echo "Bitte PIN eingeben mit: mmcli -i 0 --pin=XXXX"
    fi
else
    echo -e "${YELLOW}⚠ Kein Modem erkannt${NC}"
    echo "Bitte USB-Modem anschließen und ModemManager neu starten:"
    echo "  sudo systemctl restart ModemManager"
    echo "  mmcli -L"
fi

echo ""
echo -e "${GREEN}Installation abgeschlossen!${NC}"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "Nächste Schritte:"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "1. Konfiguration anpassen (optional):"
echo "   sudo nano /etc/sms-monitor/config.json"
echo ""
echo "2. Service starten:"
echo "   sudo systemctl enable sms-monitor"
echo "   sudo systemctl start sms-monitor"
echo ""
echo "3. Status prüfen:"
echo "   sudo systemctl status sms-monitor"
echo "   sudo journalctl -u sms-monitor -f"
echo ""
echo "4. CLI-Tool verwenden:"
echo "   sms-monitor --help"
echo "   sms-monitor check      # SMS manuell prüfen"
echo "   sms-monitor list       # Gespeicherte SMS anzeigen"
echo "   sms-monitor stats      # Statistiken"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo ""
