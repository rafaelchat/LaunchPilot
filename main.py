#!/usr/bin/env python3
import sys
import os

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Adiciona o diretório base ao sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from launchpilot.cli import main

if __name__ == "__main__":
    main()
