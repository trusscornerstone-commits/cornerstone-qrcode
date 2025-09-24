import csv
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

# Ajuste este import conforme o local do seu modelo Truss
# Supondo que esteja em apps/django_apps/accounts/models.py
from apps.django_apps.accounts.models import Truss


class Command(BaseCommand):
    help = "Importa/atualiza registros de Truss a partir de um CSV. Preserva o ID do CSV como PK."

    def add_arguments(self, parser):
        parser.add_argument("--csv", dest="csv_path", required=True, help="Caminho do arquivo CSV")
        parser.add_argument("--delimiter", dest="delimiter", default=",", help="Delimitador (padrão: ,)")

    def handle(self, *args, **opts):
        csv_path = opts["csv_path"]
        delimiter = opts["delimiter"]

        created, updated, errors = 0, 0, 0
        self.stdout.write(self.style.NOTICE(f"[import_trusses] Lendo {csv_path} ..."))

        try:
            with open(csv_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter=delimiter)
                with transaction.atomic():
                    for row in reader:
                        try:
                            pk = int(row.get("id"))
                        except Exception:
                            errors += 1
                            continue

                        # Mapeie os campos do seu CSV para o modelo
                        defaults = {
                            "job_number": row.get("job_number") or "",
                            "truss_number": str(row.get("truss_number") or ""),
                            "tipo": row.get("tipo") or "",
                            "quantidade": int(row.get("quantidade") or 0) if str(row.get("quantidade") or "").isdigit() else None,
                            "ply": int(row.get("ply") or 0) if str(row.get("ply") or "").isdigit() else None,
                            "endereco": row.get("endereco") or "",
                            "tamanho": row.get("tamanho") or "",
                            "status": row.get("status") or "",
                        }

                        obj, created_flag = Truss.objects.update_or_create(
                            id=pk,  # preserva o ID do CSV como chave primária
                            defaults=defaults,
                        )
                        if created_flag:
                            created += 1
                        else:
                            updated += 1

        except FileNotFoundError:
            raise CommandError(f"CSV não encontrado: {csv_path}")

        self.stdout.write(self.style.SUCCESS(
            f"[import_trusses] Concluído — criados: {created}, atualizados: {updated}, erros: {errors}"
        ))