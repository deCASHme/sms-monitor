"""
SMS Monitor - USB Modem SMS Empfang mit ModemManager
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Ein einfaches Python-Tool zum Empfangen und Verwalten von SMS
über USB 4G/LTE Modems unter Linux mit ModemManager.

:copyright: (c) 2025 deCASHme
:license: MIT
"""

__version__ = "1.0.0"
__author__ = "deCASHme"

from .monitor import SMSMonitor
from .config import Config

__all__ = ["SMSMonitor", "Config"]
