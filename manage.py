#!/usr/bin/env python
import os
import sys
from pathlib import Path
from django.contrib.auth import get_user_model

# Carrega .env automaticamente (dev)
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=True)
except Exception:
    pass


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cornerstone.settings')

    from django.core.management import execute_from_command_line

    # ⚙️ Criação automática de superusuário se variável de ambiente permitir
    if os.environ.get("CREATE_SUPERUSER") == "1":
        try:
            import django
            django.setup()
            User = get_user_model()
            username = os.environ.get("SUPERUSER_USERNAME", "admin")
            email = os.environ.get("SUPERUSER_EMAIL", "admin@example.com")
            password = os.environ.get("SUPERUSER_PASSWORD", "admin123")

            if not User.objects.filter(username=username).exists():
                User.objects.create_superuser(username=username, email=email, password=password)
                print(f"✅ Superusuário '{username}' criado automaticamente.")
            else:
                # Opcional: força reset da senha se SUPERUSER_FORCE_RESET=1
                if os.environ.get("SUPERUSER_FORCE_RESET") == "1":
                    user = User.objects.get(username=username)
                    user.set_password(password)
                    user.save()
                    print(f"🔁 Senha do superusuário '{username}' redefinida.")
        except Exception as e:
            print(f"⚠️ Aviso: não foi possível criar o superusuário automaticamente: {e}")

    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
