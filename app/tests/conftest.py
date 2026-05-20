"""Добавляет корень приложения (lab-1/app) в sys.path для импорта пакета src."""

import sys
from pathlib import Path

_APP_ROOT = Path(__file__).resolve().parents[1]
if str(_APP_ROOT) not in sys.path:
    sys.path.insert(0, str(_APP_ROOT))
