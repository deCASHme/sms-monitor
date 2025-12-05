"""
SMS Monitor - Hauptmodul für SMS-Empfang über ModemManager
"""

import json
import logging
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

try:
    import gi
    gi.require_version('ModemManager', '1.0')
    from gi.repository import ModemManager, GLib, Gio
except ImportError:
    print("FEHLER: ModemManager GObject Introspection nicht gefunden!")
    print("Installation: sudo apt install python3-gi gir1.2-modemmanager-1.0")
    sys.exit(1)

from .config import Config


class SMSMonitor:
    """
    SMS-Monitor für ModemManager-kompatible USB-Modems

    Empfängt, speichert und verwaltet SMS-Nachrichten von USB 4G/LTE Modems.
    """

    def __init__(self, config: Config = None):
        """
        Initialisiert den SMS-Monitor

        Args:
            config: Config-Objekt (optional)
        """
        self.config = config or Config()
        self.setup_logging()
        self.setup_directories()
        self.processed_sms = self._load_processed()
        self.modem = None
        self.messaging = None
        self.running = True

        self.logger.info("SMS-Monitor initialisiert")

    def setup_logging(self):
        """Logging-System konfigurieren"""
        handlers = []

        # File Handler
        log_file = Path(self.config.get('log_file'))
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(
            logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
        )
        handlers.append(file_handler)

        # Console Handler
        if self.config.get('enable_console_output', True):
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(
                logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
            )
            handlers.append(console_handler)

        # Logger konfigurieren
        log_level = getattr(logging, self.config.get('log_level', 'INFO').upper())
        logging.basicConfig(level=log_level, handlers=handlers)
        self.logger = logging.getLogger(__name__)

    def setup_directories(self):
        """Benötigte Verzeichnisse erstellen"""
        sms_dir = Path(self.config.get('sms_dir'))
        sms_dir.mkdir(parents=True, exist_ok=True)

        processed_db = Path(self.config.get('processed_db'))
        processed_db.parent.mkdir(parents=True, exist_ok=True)

        self.logger.debug("Verzeichnisse eingerichtet")

    def _load_processed(self) -> Dict:
        """
        Datenbank verarbeiteter SMS laden

        Returns:
            Dictionary mit verarbeiteten SMS
        """
        try:
            processed_file = Path(self.config.get('processed_db'))
            if processed_file.exists():
                with open(processed_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"Processed-DB konnte nicht geladen werden: {e}")

        return {}

    def _save_processed(self):
        """Datenbank verarbeiteter SMS speichern"""
        try:
            processed_file = Path(self.config.get('processed_db'))
            with open(processed_file, 'w', encoding='utf-8') as f:
                json.dump(self.processed_sms, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Fehler beim Speichern der Processed-DB: {e}")

    def connect_modem(self) -> bool:
        """
        Verbindung zum Modem herstellen

        Returns:
            True wenn erfolgreich, False bei Fehler
        """
        try:
            # System-Bus verbinden
            bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)

            # ModemManager ObjectManager
            manager_proxy = Gio.DBusProxy.new_sync(
                bus,
                Gio.DBusProxyFlags.NONE,
                None,
                'org.freedesktop.ModemManager1',
                '/org/freedesktop/ModemManager1',
                'org.freedesktop.DBus.ObjectManager',
                None
            )

            # Alle verwalteten Objekte abrufen
            result = manager_proxy.call_sync(
                'GetManagedObjects',
                None,
                Gio.DBusCallFlags.NONE,
                -1,
                None
            )

            # Modem-Pfade extrahieren
            objects = result[0]
            modem_paths = [path for path in objects.keys() if '/Modem/' in path]

            if not modem_paths:
                self.logger.error("Kein Modem gefunden. Ist das USB-Modem angeschlossen?")
                return False

            modem_index = self.config.get('modem_index', 0)
            if modem_index >= len(modem_paths):
                self.logger.error(
                    f"Modem-Index {modem_index} ungültig. "
                    f"Verfügbare Modems: {len(modem_paths)}"
                )
                return False

            modem_path = modem_paths[modem_index]

            # Modem-Proxy erstellen
            self.modem_proxy = Gio.DBusProxy.new_sync(
                bus,
                Gio.DBusProxyFlags.NONE,
                None,
                'org.freedesktop.ModemManager1',
                modem_path,
                'org.freedesktop.ModemManager1.Modem',
                None
            )

            # Messaging-Proxy erstellen
            self.messaging_proxy = Gio.DBusProxy.new_sync(
                bus,
                Gio.DBusProxyFlags.NONE,
                None,
                'org.freedesktop.ModemManager1',
                modem_path,
                'org.freedesktop.ModemManager1.Modem.Messaging',
                None
            )

            # Modem-Informationen abrufen
            manufacturer = self.modem_proxy.get_cached_property('Manufacturer')
            model = self.modem_proxy.get_cached_property('Model')

            if manufacturer and model:
                manufacturer_str = manufacturer.unpack() if hasattr(manufacturer, 'unpack') else str(manufacturer)
                model_str = model.unpack() if hasattr(model, 'unpack') else str(model)
                self.logger.info(f"Modem verbunden: {manufacturer_str} {model_str}")
            else:
                self.logger.info(f"Modem verbunden: {modem_path}")

            # Für Kompatibilität
            self.modem = self.modem_proxy
            self.messaging = self.messaging_proxy
            self.modem_path = modem_path

            return True

        except Exception as e:
            self.logger.error(f"Modem-Verbindung fehlgeschlagen: {e}")
            return False

    def get_sms_list(self) -> List:
        """
        Liste aller SMS vom Modem abrufen

        Returns:
            Liste von SMS-Pfaden
        """
        try:
            if not self.messaging:
                self.logger.error("Messaging-Interface nicht verfügbar")
                return []

            # DBus-Call: List() Methode aufrufen
            result = self.messaging_proxy.call_sync(
                'List',
                None,
                Gio.DBusCallFlags.NONE,
                -1,
                None
            )

            # Ergebnis extrahieren (Liste von SMS-Pfaden)
            sms_paths = result[0] if result else []
            return sms_paths

        except Exception as e:
            self.logger.error(f"SMS-Liste konnte nicht abgerufen werden: {e}")
            return []

    def parse_sms(self, sms_path: str) -> Optional[Dict]:
        """
        SMS-Daten extrahieren

        Args:
            sms_path: DBus-Pfad zur SMS

        Returns:
            Dictionary mit SMS-Daten oder None bei Fehler
        """
        try:
            # System-Bus
            bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)

            # SMS-Proxy erstellen
            sms_proxy = Gio.DBusProxy.new_sync(
                bus,
                Gio.DBusProxyFlags.NONE,
                None,
                'org.freedesktop.ModemManager1',
                sms_path,
                'org.freedesktop.ModemManager1.Sms',
                None
            )

            # Properties abrufen
            number = sms_proxy.get_cached_property('Number')
            text = sms_proxy.get_cached_property('Text')
            timestamp = sms_proxy.get_cached_property('Timestamp')
            state = sms_proxy.get_cached_property('State')

            return {
                'path': sms_path,
                'number': number.unpack() if number else '',
                'text': text.unpack() if text else '',
                'timestamp': timestamp.unpack() if timestamp else '',
                'state': state.unpack() if state else 0
            }
        except Exception as e:
            self.logger.error(f"SMS-Parsing fehlgeschlagen: {e}")
            return None

    def is_processed(self, sms_data: Dict) -> bool:
        """
        Prüfen ob SMS bereits verarbeitet wurde

        Args:
            sms_data: SMS-Daten

        Returns:
            True wenn bereits verarbeitet
        """
        key = f"{sms_data['number']}_{sms_data['timestamp']}"
        return key in self.processed_sms

    def save_sms(self, sms_data: Dict) -> Optional[Path]:
        """
        SMS in Datei speichern

        Args:
            sms_data: SMS-Daten

        Returns:
            Pfad zur gespeicherten Datei oder None bei Fehler
        """
        try:
            # Sicheren Dateinamen generieren
            timestamp_str = sms_data['timestamp']
            try:
                # ISO 8601 Timestamp parsen
                dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                time_part = dt.strftime('%Y%m%d_%H%M%S')
            except:
                # Fallback: Aktueller Timestamp
                time_part = datetime.now().strftime('%Y%m%d_%H%M%S')

            # Telefonnummer sanitieren
            number = sms_data['number'].replace('+', '').replace(' ', '')

            filename = f"{time_part}_{number}.txt"
            sms_dir = Path(self.config.get('sms_dir'))
            filepath = sms_dir / filename

            # SMS speichern
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"Von: {sms_data['number']}\n")
                f.write(f"Zeit: {sms_data['timestamp']}\n")
                f.write(f"Status: {sms_data['state']}\n")
                f.write(f"\nNachricht:\n")
                f.write(f"{sms_data['text']}\n")

            self.logger.info(f"SMS gespeichert: {filepath}")

            # Als verarbeitet markieren
            key = f"{sms_data['number']}_{sms_data['timestamp']}"
            self.processed_sms[key] = {
                'saved_at': datetime.now().isoformat(),
                'filepath': str(filepath),
                'from': sms_data['number']
            }
            self._save_processed()

            return filepath

        except Exception as e:
            self.logger.error(f"SMS-Speicherung fehlgeschlagen: {e}")
            return None

    def delete_sms(self, sms_path: str) -> bool:
        """
        SMS vom Modem löschen

        Args:
            sms_path: D-Bus Pfad der SMS

        Returns:
            True wenn erfolgreich
        """
        try:
            if not self.messaging:
                return False

            # DBus-Call: Delete() Methode aufrufen
            self.messaging_proxy.call_sync(
                'Delete',
                GLib.Variant('(o)', (sms_path,)),
                Gio.DBusCallFlags.NONE,
                -1,
                None
            )
            self.logger.debug(f"SMS vom Modem gelöscht: {sms_path}")
            return True

        except Exception as e:
            self.logger.error(f"SMS-Löschung fehlgeschlagen: {e}")
            return False

    def notify_webhooks(self, sms_data: Dict):
        """
        Webhook-Benachrichtigungen senden

        Args:
            sms_data: SMS-Daten
        """
        webhooks = self.config.get('webhooks', [])
        if not webhooks:
            return

        try:
            import requests
        except ImportError:
            self.logger.warning(
                "requests-Bibliothek nicht installiert, Webhooks deaktiviert. "
                "Installation: pip install requests"
            )
            return

        payload = {
            'from': sms_data['number'],
            'text': sms_data['text'],
            'timestamp': sms_data['timestamp'],
            'received_at': datetime.now().isoformat()
        }

        for webhook_url in webhooks:
            try:
                response = requests.post(
                    webhook_url,
                    json=payload,
                    timeout=5,
                    headers={'Content-Type': 'application/json'}
                )
                response.raise_for_status()
                self.logger.info(f"Webhook benachrichtigt: {webhook_url}")

            except Exception as e:
                self.logger.error(f"Webhook-Fehler ({webhook_url}): {e}")

    def process_sms(self):
        """Alle neuen SMS verarbeiten"""
        sms_list = self.get_sms_list()

        if not sms_list:
            self.logger.debug("Keine SMS im Modem-Speicher")
            return

        for sms in sms_list:
            sms_data = self.parse_sms(sms)

            if not sms_data:
                continue

            # Bereits verarbeitet?
            if self.is_processed(sms_data):
                self.logger.debug(f"SMS bereits verarbeitet: {sms_data['path']}")
                continue

            # Neue SMS gefunden
            self.logger.info("=" * 50)
            self.logger.info("NEUE SMS EMPFANGEN")
            self.logger.info(f"Von: {sms_data['number']}")
            self.logger.info(f"Zeit: {sms_data['timestamp']}")
            self.logger.info(f"Text: {sms_data['text']}")
            self.logger.info("=" * 50)

            # SMS speichern
            filepath = self.save_sms(sms_data)

            # Webhooks benachrichtigen
            if filepath:
                self.notify_webhooks(sms_data)

            # SMS vom Modem löschen
            if self.config.get('delete_after_read', True):
                self.delete_sms(sms_data['path'])

    def run(self):
        """
        Hauptloop des SMS-Monitors

        Läuft kontinuierlich und prüft in konfigurierten Intervallen auf neue SMS.
        """
        self.logger.info("SMS-Monitor wird gestartet...")

        # Signal Handler für sauberes Beenden
        def signal_handler(sig, frame):
            self.logger.info(f"Signal {sig} empfangen, beende Monitor...")
            self.running = False

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Modem verbinden
        if not self.connect_modem():
            self.logger.error("Modem-Verbindung fehlgeschlagen, Programm wird beendet")
            sys.exit(1)

        self.logger.info("SMS-Monitor läuft. Drücke Strg+C zum Beenden.")

        # Hauptloop
        check_interval = self.config.get('check_interval', 30)

        while self.running:
            try:
                self.process_sms()
                time.sleep(check_interval)

            except KeyboardInterrupt:
                self.logger.info("Beenden durch Benutzer...")
                break

            except Exception as e:
                self.logger.error(f"Fehler im Hauptloop: {e}", exc_info=True)
                time.sleep(10)  # Kurze Pause bei Fehlern

        self.logger.info("SMS-Monitor wurde beendet")
