#!/usr/bin/env python
import os
import sys
from pathlib import Path

# Carrega .env automaticamente (dev)
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent / ".env"
    if env_path.exists():
        # Força sobrescrever variáveis existentes com as do .env
        load_dotenv(env_path, override=True)
except Exception:
    pass

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cornerstone.settings')
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()