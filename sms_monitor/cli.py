#!/usr/bin/env python3
"""
SMS Monitor - CLI Tool
~~~~~~~~~~~~~~~~~~~~~~

Kommandozeilen-Tool für manuelle SMS-Abfragen und Verwaltung
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

from .config import Config
from .monitor import SMSMonitor


def cmd_run(args):
    """SMS-Monitor im Daemon-Modus starten"""
    config = Config(args.config)
    monitor = SMSMonitor(config)
    monitor.run()


def cmd_check(args):
    """Einmalige SMS-Prüfung durchführen"""
    config = Config(args.config)
    monitor = SMSMonitor(config)

    if not monitor.connect_modem():
        print("FEHLER: Modem-Verbindung fehlgeschlagen")
        sys.exit(1)

    print("Prüfe auf neue SMS...")
    monitor.process_sms()
    print("Fertig.")


def cmd_list(args):
    """Alle gespeicherten SMS auflisten"""
    config = Config(args.config)
    sms_dir = Path(config.get('sms_dir'))

    if not sms_dir.exists():
        print(f"SMS-Verzeichnis nicht gefunden: {sms_dir}")
        return

    sms_files = sorted(sms_dir.glob("*.txt"))

    if not sms_files:
        print("Keine gespeicherten SMS vorhanden")
        return

    print(f"\n=== {len(sms_files)} gespeicherte SMS ===\n")

    for sms_file in sms_files:
        if args.verbose:
            print(f"{'=' * 70}")
            print(f"Datei: {sms_file.name}")
            print(f"{'=' * 70}")
            print(sms_file.read_text(encoding='utf-8'))
            print()
        else:
            # Nur die erste Zeile (Von:) anzeigen
            with open(sms_file, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
            print(f"{sms_file.name}: {first_line}")


def cmd_stats(args):
    """Statistiken anzeigen"""
    config = Config(args.config)
    monitor = SMSMonitor(config)

    sms_dir = Path(config.get('sms_dir'))
    sms_count = len(list(sms_dir.glob("*.txt"))) if sms_dir.exists() else 0

    processed = monitor._load_processed()

    print("\n=== SMS Monitor Statistiken ===\n")
    print(f"Verarbeitete SMS (gesamt): {len(processed)}")
    print(f"Gespeicherte SMS-Dateien:  {sms_count}")
    print(f"SMS-Verzeichnis:           {sms_dir}")
    print(f"Log-Datei:                 {config.get('log_file')}")
    print(f"Konfiguration:             {config.config_path}")
    print(f"Check-Intervall:           {config.get('check_interval')}s")
    print(f"Löschen nach Lesen:        {config.get('delete_after_read')}")

    # Modem-Info (falls verfügbar)
    if monitor.connect_modem():
        print(f"\nModem:")
        print(f"  Hersteller: {monitor.modem.get_manufacturer()}")
        print(f"  Modell:     {monitor.modem.get_model()}")
        print(f"  Firmware:   {monitor.modem.get_revision()}")

    print()


def cmd_modem_info(args):
    """Detaillierte Modem-Informationen anzeigen"""
    config = Config(args.config)
    monitor = SMSMonitor(config)

    if not monitor.connect_modem():
        print("FEHLER: Modem-Verbindung fehlgeschlagen")
        sys.exit(1)

    modem = monitor.modem

    print("\n=== Modem-Informationen ===\n")
    print(f"Hersteller:  {modem.get_manufacturer()}")
    print(f"Modell:      {modem.get_model()}")
    print(f"Firmware:    {modem.get_revision()}")

    try:
        print(f"Equipment ID: {modem.get_equipment_identifier()}")
    except:
        pass

    try:
        state = modem.get_state()
        print(f"Status:      {state}")
    except:
        pass

    try:
        signal_quality = modem.get_signal_quality()
        print(f"Signalstärke: {signal_quality}%")
    except:
        pass

    print()


def cmd_config(args):
    """Konfiguration verwalten"""
    if args.create_example:
        config = Config()
        example_path = args.create_example
        config.create_example_config(example_path)
        print(f"Beispiel-Konfiguration erstellt: {example_path}")
        return

    config = Config(args.config)

    if args.show:
        print("\n=== Aktuelle Konfiguration ===\n")
        import json
        print(json.dumps(config.data, indent=2))
        print()


def main():
    """Haupteinstiegspunkt für CLI"""
    parser = argparse.ArgumentParser(
        description='SMS Monitor - SMS-Empfang über USB-Modem',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  %(prog)s run                    # Monitor starten
  %(prog)s check                  # Einmalig auf SMS prüfen
  %(prog)s list                   # Gespeicherte SMS anzeigen
  %(prog)s stats                  # Statistiken anzeigen
  %(prog)s modem-info             # Modem-Informationen
  %(prog)s config --show          # Konfiguration anzeigen

Weitere Informationen: https://github.com/deCASHme/sms-monitor
        """
    )

    parser.add_argument(
        '-c', '--config',
        default='/etc/sms-monitor/config.json',
        help='Pfad zur Konfigurationsdatei (Standard: /etc/sms-monitor/config.json)'
    )

    parser.add_argument(
        '-v', '--version',
        action='version',
        version='SMS Monitor 1.0.0'
    )

    subparsers = parser.add_subparsers(dest='command', help='Verfügbare Befehle')

    # run command
    parser_run = subparsers.add_parser('run', help='Monitor starten (Daemon-Modus)')
    parser_run.set_defaults(func=cmd_run)

    # check command
    parser_check = subparsers.add_parser('check', help='Einmalig auf SMS prüfen')
    parser_check.set_defaults(func=cmd_check)

    # list command
    parser_list = subparsers.add_parser('list', help='Gespeicherte SMS anzeigen')
    parser_list.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Komplette SMS-Inhalte anzeigen'
    )
    parser_list.set_defaults(func=cmd_list)

    # stats command
    parser_stats = subparsers.add_parser('stats', help='Statistiken anzeigen')
    parser_stats.set_defaults(func=cmd_stats)

    # modem-info command
    parser_modem = subparsers.add_parser('modem-info', help='Modem-Informationen')
    parser_modem.set_defaults(func=cmd_modem_info)

    # config command
    parser_config = subparsers.add_parser('config', help='Konfiguration verwalten')
    parser_config.add_argument(
        '--show',
        action='store_true',
        help='Aktuelle Konfiguration anzeigen'
    )
    parser_config.add_argument(
        '--create-example',
        metavar='PATH',
        help='Beispiel-Konfiguration erstellen'
    )
    parser_config.set_defaults(func=cmd_config)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Funktion ausführen
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\nAbgebrochen durch Benutzer")
        sys.exit(0)
    except Exception as e:
        print(f"FEHLER: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
