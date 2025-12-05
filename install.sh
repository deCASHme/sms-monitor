#!/bin/bash
#
# SMS Monitor Installation Script
# ================================
#
# Installiert den SMS Monitor nach /opt/sms-monitor mit eigenem Virtual Environment
#

set -e

INSTALL_DIR="/opt/sms-monitor"
CONFIG_DIR="/etc/sms-monitor"
BIN_LINK="/usr/local/bin/sms-monitor"

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

# Prüfen ob bereits installiert
if [ -d "$INSTALL_DIR" ]; then
    echo -e "${YELLOW}Warnung: SMS Monitor ist bereits installiert in $INSTALL_DIR${NC}"
    echo ""
    read -p "Backup erstellen und neu installieren? (j/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Jj]$ ]]; then
        BACKUP_DIR="${INSTALL_DIR}.backup.$(date +%Y%m%d_%H%M%S)"
        echo "Erstelle Backup in $BACKUP_DIR..."
        mv "$INSTALL_DIR" "$BACKUP_DIR"
        echo -e "${GREEN}Backup erstellt${NC}"
    else
        echo "Installation abgebrochen"
        exit 0
    fi
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
apt install -y python3 python3-venv python3-pip python3-gi gir1.2-modemmanager-1.0 modemmanager libqmi-utils

echo ""
echo "2. Installations-Verzeichnis erstellen..."
mkdir -p "$INSTALL_DIR"

# Projekt-Dateien kopieren
echo ""
echo "3. Projekt-Dateien kopieren..."
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cp -r "$SCRIPT_DIR/sms_monitor" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/setup.py" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/requirements.txt" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/README.md" "$INSTALL_DIR/" 2>/dev/null || true
cp "$SCRIPT_DIR/LICENSE" "$INSTALL_DIR/" 2>/dev/null || true

echo "  ✓ Dateien kopiert nach $INSTALL_DIR"

# Virtual Environment erstellen
echo ""
echo "4. Virtual Environment erstellen..."
cd "$INSTALL_DIR"
python3 -m venv venv
echo "  ✓ venv erstellt"

# Python-Pakete installieren
echo ""
echo "5. Python-Abhängigkeiten installieren..."
source venv/bin/activate
pip install --upgrade pip
pip install PyGObject requests
pip install -e .
deactivate
echo "  ✓ Abhängigkeiten installiert"

# Symlink erstellen
echo ""
echo "6. CLI-Tool verlinken..."
ln -sf "$INSTALL_DIR/venv/bin/sms-monitor" "$BIN_LINK"
echo "  ✓ Symlink erstellt: $BIN_LINK"

# Konfigurationsverzeichnis erstellen
echo ""
echo "7. Konfiguration erstellen..."
mkdir -p "$CONFIG_DIR"

if [ ! -f "$CONFIG_DIR/config.json" ]; then
    if [ -f "$SCRIPT_DIR/examples/config.json" ]; then
        cp "$SCRIPT_DIR/examples/config.json" "$CONFIG_DIR/config.json"
        echo "  ✓ Konfigurationsdatei erstellt: $CONFIG_DIR/config.json"
    else
        # Fallback: Minimal-Konfiguration erstellen
        cat > "$CONFIG_DIR/config.json" << 'EOF'
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
EOF
        echo "  ✓ Standard-Konfiguration erstellt"
    fi
else
    echo "  ⊗ Konfiguration existiert bereits: $CONFIG_DIR/config.json"
fi

# Verzeichnisse für SMS und Logs erstellen
echo ""
echo "8. Daten-Verzeichnisse erstellen..."
mkdir -p /var/spool/sms
mkdir -p /var/lib/sms-monitor
mkdir -p /var/log
touch /var/log/sms-monitor.log
echo "  ✓ Verzeichnisse erstellt"

# Systemd Service installieren
echo ""
echo "9. Systemd Service installieren..."
if [ -f "$SCRIPT_DIR/systemd/sms-monitor.service" ]; then
    cp "$SCRIPT_DIR/systemd/sms-monitor.service" /etc/systemd/system/
    systemctl daemon-reload
    echo "  ✓ Service installiert"
else
    echo "  ⚠ Service-Datei nicht gefunden"
fi

# ModemManager starten
echo ""
echo "10. ModemManager starten..."
systemctl enable ModemManager
systemctl start ModemManager
echo "  ✓ ModemManager gestartet"

# Modem-Check
echo ""
echo "11. Modem-Status prüfen..."
sleep 2

if mmcli -L 2>/dev/null | grep -q "Modem"; then
    echo -e "${GREEN}  ✓ Modem erkannt${NC}"
    mmcli -L

    echo ""
    echo "Modem-Details:"
    mmcli -m 0 2>/dev/null | grep -E "manufacturer|model|state|lock" || true

    if mmcli -m 0 2>/dev/null | grep -q "lock: sim-pin"; then
        echo ""
        echo -e "${YELLOW}  ⚠ Modem ist mit SIM-PIN gesperrt${NC}"
        echo "Bitte PIN eingeben mit: mmcli -i 0 --pin=XXXX"
    fi
else
    echo -e "${YELLOW}  ⚠ Kein Modem erkannt${NC}"
    echo "Bitte USB-Modem anschließen und ModemManager neu starten:"
    echo "  sudo systemctl restart ModemManager"
    echo "  mmcli -L"
fi

echo ""
echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo -e "${GREEN}Installation abgeschlossen!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo ""
echo "Installations-Pfad: $INSTALL_DIR"
echo "Konfiguration:      $CONFIG_DIR/config.json"
echo "CLI-Tool:           $BIN_LINK"
echo ""
echo "Nächste Schritte:"
echo "═══════════════════════════════════════════"
echo ""
echo "1. Konfiguration anpassen (optional):"
echo "   sudo nano $CONFIG_DIR/config.json"
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
echo "═══════════════════════════════════════════"
echo ""
