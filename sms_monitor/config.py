"""
Konfigurationsmanagement für SMS Monitor
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any


class Config:
    """Konfigurationsverwaltung"""

    DEFAULT_CONFIG = {
        "modem_index": 0,
        "sms_dir": "/var/spool/sms",
        "log_file": "/var/log/sms-monitor.log",
        "log_level": "INFO",
        "processed_db": "/var/lib/sms-monitor/processed.json",
        "check_interval": 30,
        "delete_after_read": True,
        "webhooks": [],
        "enable_console_output": True
    }

    def __init__(self, config_path: str = "/etc/sms-monitor/config.json"):
        """
        Initialisiert die Konfiguration

        Args:
            config_path: Pfad zur Konfigurationsdatei
        """
        self.config_path = config_path
        self.data = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Konfiguration aus Datei laden"""
        config = self.DEFAULT_CONFIG.copy()

        try:
            config_file = Path(self.config_path)
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    config.update(user_config)
                logging.debug(f"Konfiguration geladen von {self.config_path}")
            else:
                logging.warning(
                    f"Konfigurationsdatei {self.config_path} nicht gefunden, "
                    f"verwende Standard-Konfiguration"
                )
        except Exception as e:
            logging.error(f"Fehler beim Laden der Konfiguration: {e}")

        return config

    def get(self, key: str, default: Any = None) -> Any:
        """
        Konfigurationswert abrufen

        Args:
            key: Konfigurationsschlüssel
            default: Standardwert falls Schlüssel nicht existiert

        Returns:
            Konfigurationswert
        """
        return self.data.get(key, default)

    def save(self, path: str = None):
        """
        Konfiguration speichern

        Args:
            path: Pfad zum Speichern (optional, nutzt config_path falls nicht angegeben)
        """
        save_path = path or self.config_path

        try:
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            logging.info(f"Konfiguration gespeichert in {save_path}")
        except Exception as e:
            logging.error(f"Fehler beim Speichern der Konfiguration: {e}")

    def create_example_config(self, path: str):
        """
        Beispiel-Konfigurationsdatei erstellen

        Args:
            path: Pfad für die Beispieldatei
        """
        self.save(path)
        logging.info(f"Beispiel-Konfiguration erstellt: {path}")
