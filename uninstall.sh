#!/bin/bash
#
# SMS Monitor Deinstallations-Script
# ===================================
#
# Entfernt den SMS Monitor sauber vom System
#

set -e

# Farben für Ausgabe
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}SMS Monitor Deinstallation${NC}"
echo "==========================="
echo ""

# Root-Check
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Fehler: Dieses Script muss als root ausgeführt werden${NC}"
    echo "Bitte mit sudo ausführen: sudo ./uninstall.sh"
    exit 1
fi

echo -e "${YELLOW}Warnung: Dies entfernt den SMS Monitor vom System.${NC}"
echo ""
echo "Folgende Komponenten werden entfernt:"
echo "  - SMS Monitor Python-Paket"
echo "  - Systemd Service"
echo "  - CLI-Tool (/usr/local/bin/sms-monitor)"
echo ""
echo "Optional werden auch entfernt:"
echo "  - Konfigurationsdateien (/etc/sms-monitor)"
echo "  - Gespeicherte SMS (/var/spool/sms)"
echo "  - Log-Dateien (/var/log/sms-monitor.log)"
echo ""

read -p "Deinstallation fortsetzen? (j/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Jj]$ ]]; then
    echo "Deinstallation abgebrochen"
    exit 0
fi

# Backup erstellen?
echo ""
echo -e "${BLUE}Backup erstellen?${NC}"
read -p "Soll vor der Deinstallation ein Backup erstellt werden? (j/n) " -n 1 -r
echo
CREATE_BACKUP=false
if [[ $REPLY =~ ^[Jj]$ ]]; then
    CREATE_BACKUP=true
    BACKUP_DIR="/tmp/sms-monitor-backup-$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    echo -e "${GREEN}Erstelle Backup in: $BACKUP_DIR${NC}"

    # Konfiguration sichern
    if [ -d /etc/sms-monitor ]; then
        cp -r /etc/sms-monitor "$BACKUP_DIR/"
        echo "  ✓ Konfiguration gesichert"
    fi

    # SMS-Daten sichern
    if [ -d /var/spool/sms ]; then
        cp -r /var/spool/sms "$BACKUP_DIR/"
        echo "  ✓ SMS-Daten gesichert"
    fi

    # Logs sichern
    if [ -f /var/log/sms-monitor.log ]; then
        cp /var/log/sms-monitor.log "$BACKUP_DIR/"
        echo "  ✓ Logs gesichert"
    fi

    # Processed-DB sichern
    if [ -f /var/lib/sms-monitor/processed.json ]; then
        mkdir -p "$BACKUP_DIR/lib"
        cp /var/lib/sms-monitor/processed.json "$BACKUP_DIR/lib/"
        echo "  ✓ Verarbeitete SMS-Liste gesichert"
    fi

    echo -e "${GREEN}Backup erstellt!${NC}"
    echo ""
fi

# 1. Service stoppen und deaktivieren
if systemctl is-active --quiet sms-monitor 2>/dev/null; then
    echo "Stoppe SMS Monitor Service..."
    systemctl stop sms-monitor
    echo "  ✓ Service gestoppt"
fi

if systemctl is-enabled --quiet sms-monitor 2>/dev/null; then
    echo "Deaktiviere SMS Monitor Service..."
    systemctl disable sms-monitor
    echo "  ✓ Service deaktiviert"
fi

# 2. Service-Datei entfernen
if [ -f /etc/systemd/system/sms-monitor.service ]; then
    echo "Entferne Systemd Service..."
    rm -f /etc/systemd/system/sms-monitor.service
    systemctl daemon-reload
    echo "  ✓ Service-Datei entfernt"
fi

# 3. CLI-Tool entfernen
if [ -L /usr/local/bin/sms-monitor ] || [ -f /usr/local/bin/sms-monitor ]; then
    echo "Entferne CLI-Tool..."
    rm -f /usr/local/bin/sms-monitor
    echo "  ✓ CLI-Tool entfernt"
fi

# 4. Python-Paket deinstallieren
echo "Deinstalliere Python-Paket..."
pip3 uninstall -y sms-monitor 2>/dev/null || true
echo "  ✓ Python-Paket entfernt"

# 5. Konfiguration entfernen (optional)
echo ""
if [ -d /etc/sms-monitor ]; then
    read -p "Konfiguration entfernen? (/etc/sms-monitor) (j/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Jj]$ ]]; then
        rm -rf /etc/sms-monitor
        echo "  ✓ Konfiguration entfernt"
    else
        echo "  ⊗ Konfiguration beibehalten"
    fi
fi

# 6. SMS-Daten entfernen (optional)
echo ""
if [ -d /var/spool/sms ]; then
    SMS_COUNT=$(find /var/spool/sms -type f -name "*.txt" 2>/dev/null | wc -l)
    echo -e "${YELLOW}Warnung: Es sind $SMS_COUNT gespeicherte SMS vorhanden!${NC}"
    read -p "SMS-Daten wirklich löschen? (/var/spool/sms) (j/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Jj]$ ]]; then
        rm -rf /var/spool/sms
        echo "  ✓ SMS-Daten entfernt"
    else
        echo "  ⊗ SMS-Daten beibehalten"
    fi
fi

# 7. Verarbeitete SMS-Liste entfernen (optional)
echo ""
if [ -d /var/lib/sms-monitor ]; then
    read -p "Verarbeitete SMS-Liste entfernen? (/var/lib/sms-monitor) (j/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Jj]$ ]]; then
        rm -rf /var/lib/sms-monitor
        echo "  ✓ Verarbeitete SMS-Liste entfernt"
    else
        echo "  ⊗ Verarbeitete SMS-Liste beibehalten"
    fi
fi

# 8. Logs entfernen (optional)
echo ""
if [ -f /var/log/sms-monitor.log ]; then
    read -p "Log-Dateien entfernen? (/var/log/sms-monitor.log) (j/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Jj]$ ]]; then
        rm -f /var/log/sms-monitor.log
        echo "  ✓ Logs entfernt"
    else
        echo "  ⊗ Logs beibehalten"
    fi
fi

echo ""
echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo -e "${GREEN}Deinstallation abgeschlossen!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo ""

if [ "$CREATE_BACKUP" = true ]; then
    echo -e "${BLUE}Backup wurde erstellt in:${NC}"
    echo "  $BACKUP_DIR"
    echo ""
fi

# Zusammenfassung der verbleibenden Dateien
REMAINING=()
[ -d /etc/sms-monitor ] && REMAINING+=("  - /etc/sms-monitor (Konfiguration)")
[ -d /var/spool/sms ] && REMAINING+=("  - /var/spool/sms (SMS-Daten)")
[ -d /var/lib/sms-monitor ] && REMAINING+=("  - /var/lib/sms-monitor (Verarbeitete SMS)")
[ -f /var/log/sms-monitor.log ] && REMAINING+=("  - /var/log/sms-monitor.log (Logs)")

if [ ${#REMAINING[@]} -gt 0 ]; then
    echo "Folgende Dateien/Verzeichnisse wurden beibehalten:"
    printf '%s\n' "${REMAINING[@]}"
    echo ""
fi

echo "Vielen Dank für die Nutzung von SMS Monitor!"
echo ""
