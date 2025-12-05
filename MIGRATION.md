# Migrations-Anleitung

## Migration zu dediziertem Repository und /opt Installation

### Warum diese Migration?

1. **Dediziertes Repository**: SMS Monitor hat nun ein eigenes Repository auf https://github.com/deCASHme/sms-monitor statt in einem allgemeinen "opt" Repository
2. **Isolierte Installation**: Installation erfolgt nun in `/opt/sms-monitor` mit eigenem Virtual Environment statt system-weit
3. **Bessere Verwaltbarkeit**: Einfachere Updates und Deinstallation

### Was ändert sich?

#### Vorher (System-weite Installation)
- Installation: System-weit via `pip3 install -e .`
- Pfad: `/usr/local/lib/python3.x/dist-packages/`
- Service: `/usr/local/bin/sms-monitor`
- Repository: https://github.com/deCASHme/opt

#### Nachher (/opt Installation)
- Installation: `/opt/sms-monitor` mit eigenem venv
- Pfad: `/opt/sms-monitor/venv/`
- Service: `/opt/sms-monitor/venv/bin/sms-monitor`
- Repository: https://github.com/deCASHme/sms-monitor

### Migrations-Schritte

#### 1. Backup erstellen

```bash
# Konfiguration sichern
sudo cp -r /etc/sms-monitor /tmp/sms-monitor-config-backup

# SMS-Daten sichern
sudo cp -r /var/spool/sms /tmp/sms-monitor-data-backup

# Logs sichern (optional)
sudo cp /var/log/sms-monitor.log /tmp/sms-monitor-log-backup
```

#### 2. Alte Installation deinstallieren

```bash
# Service stoppen
sudo systemctl stop sms-monitor
sudo systemctl disable sms-monitor

# Mit Uninstall-Script (empfohlen)
sudo ./uninstall.sh

# ODER manuell:
sudo pip3 uninstall sms-monitor
sudo rm -f /usr/local/bin/sms-monitor
sudo rm -f /etc/systemd/system/sms-monitor.service
sudo systemctl daemon-reload
```

#### 3. Neue Version installieren

```bash
# Repository klonen oder updaten
git clone https://github.com/deCASHme/sms-monitor.git
cd sms-monitor

# ODER für Update:
cd sms-monitor
git remote set-url origin https://github.com/deCASHme/sms-monitor.git
git pull

# Neue Installation starten
sudo ./install.sh
```

#### 4. Konfiguration wiederherstellen

```bash
# Alte Konfiguration übertragen
sudo cp /tmp/sms-monitor-config-backup/config.json /etc/sms-monitor/config.json
```

#### 5. SMS-Daten wiederherstellen (optional)

```bash
# SMS-Daten zurückkopieren
sudo cp -r /tmp/sms-monitor-data-backup/* /var/spool/sms/
```

#### 6. Service starten und testen

```bash
# Service aktivieren und starten
sudo systemctl enable sms-monitor
sudo systemctl start sms-monitor

# Status prüfen
sudo systemctl status sms-monitor

# Logs prüfen
sudo journalctl -u sms-monitor -f

# CLI-Tool testen
sms-monitor modem-info
sms-monitor stats
```

### Wichtige Hinweise

#### Konfiguration

Die Konfigurationsdatei `/etc/sms-monitor/config.json` bleibt gleich und ist kompatibel. Alle Einstellungen bleiben erhalten.

#### SMS-Daten

Alle gespeicherten SMS in `/var/spool/sms` bleiben kompatibel und können einfach übernommen werden.

#### Systemd Service

Der neue Service nutzt den `/opt/sms-monitor/venv/bin/sms-monitor` Pfad. Dies wird automatisch vom Installations-Script konfiguriert.

### Neuinstallation

Für neue Installationen ohne vorherige Version:

```bash
# Repository klonen
git clone https://github.com/deCASHme/sms-monitor.git
cd sms-monitor

# Installieren
sudo ./install.sh

# Konfiguration anpassen (optional)
sudo nano /etc/sms-monitor/config.json

# Service starten
sudo systemctl enable sms-monitor
sudo systemctl start sms-monitor
```

### Fehlerbehebung

#### Service startet nicht

```bash
# Logs prüfen
sudo journalctl -u sms-monitor -n 50

# Python-Pfad prüfen
/opt/sms-monitor/venv/bin/python3 --version

# Virtual Environment prüfen
ls -la /opt/sms-monitor/venv/
```

#### CLI-Tool nicht verfügbar

```bash
# Symlink prüfen
ls -la /usr/local/bin/sms-monitor

# Sollte zeigen auf: /opt/sms-monitor/venv/bin/sms-monitor

# Falls nicht vorhanden, manuell erstellen:
sudo ln -sf /opt/sms-monitor/venv/bin/sms-monitor /usr/local/bin/sms-monitor
```

#### Modem-Verbindung fehlgeschlagen

```bash
# ModemManager Status
sudo systemctl status ModemManager

# Modem erkennen
mmcli -L

# Modem-Details
mmcli -m 0
```

### Rollback

Falls Probleme auftreten und Sie zur alten Version zurück möchten:

```bash
# Neue Installation entfernen
sudo /opt/sms-monitor/uninstall.sh

# Alte Version wiederherstellen
cd /path/to/old/sms-monitor
sudo ./install.sh

# Konfiguration zurückkopieren
sudo cp /tmp/sms-monitor-config-backup/config.json /etc/sms-monitor/config.json
```

### Support

Bei Problemen:
- GitHub Issues: https://github.com/deCASHme/sms-monitor/issues
- Logs prüfen: `sudo journalctl -u sms-monitor -f`
- Modem-Status: `sms-monitor modem-info`

### Änderungshistorie

- **v1.0.0**: Initiales Release mit /opt Installation
- Vorherige Versionen: System-weite Installation in deCASHme/opt Repository
