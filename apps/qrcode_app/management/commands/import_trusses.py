import csv
from contextlib import contextmanager
from typing import Optional, List

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, connection
from django.db.utils import IntegrityError

# ATENÇÃO: ajuste este import para onde seu modelo Truss realmente está.
# Ex.: from apps.qrcode_app.models import Truss
from apps.django_apps.accounts.models import Truss


class Command(BaseCommand):
    help = "Importa/atualiza registros de Truss a partir de um CSV. Preserva o ID do CSV como PK."

    def add_arguments(self, parser):
        parser.add_argument("--csv", dest="csv_path", required=True, help="Caminho do arquivo CSV")
        parser.add_argument("--delimiter", dest="delimiter", default=",", help="Delimitador (padrão: ,)")
        parser.add_argument("--dry-run", action="store_true", help="Valida e conta, mas não escreve no banco")

    def handle(self, *args, **opts):
        csv_path = opts["csv_path"]
        delimiter = opts["delimiter"]
        dry_run = bool(opts.get("dry_run"))

        created, updated, errors = 0, 0, 0
        error_lines: List[str] = []
        max_error_lines = 20

        self.stdout.write(self.style.NOTICE(f"[import_trusses] Lendo {csv_path} ... (dry-run={dry_run})"))

        # Colunas esperadas
        required_columns = {"id"}
        optional_columns = {
            "job_number",
            "truss_number",
            "tipo",
            "quantidade",
            "ply",
            "endereco",
            "tamanho",
            "status",
        }

        def to_int_or_none(value: Optional[str]) -> Optional[int]:
            if value is None:
                return None
            s = str(value).strip()
            if s == "":
                return None
            try:
                return int(s)
            except ValueError:
                return None

        def table_exists(model) -> bool:
            try:
                with connection.cursor():
                    tables = set(connection.introspection.table_names())
                return model._meta.db_table in tables
            except Exception:
                # Em casos muito raros de connection failure, considere que não existe
                return False

        # Se o CSV tem valores decimais em 'ply' (ex.: 1.2), e seu modelo não aceita null,
        # ajuste o modelo (FloatField/DecimalField) OU converta aqui para inteiro/0 conforme sua regra.
        try:
            with open(csv_path, newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f, delimiter=delimiter)

                if not reader.fieldnames:
                    raise CommandError("Cabeçalho não encontrado no CSV.")

                header = set([h.strip() for h in reader.fieldnames if h])
                missing = required_columns - header
                if missing:
                    raise CommandError(f"Colunas obrigatórias ausentes no CSV: {', '.join(sorted(missing))}")

                extras = header - (required_columns | optional_columns)
                if extras:
                    self.stdout.write(self.style.WARNING(
                        f"[import_trusses] Aviso: colunas extras ignoradas: {', '.join(sorted(extras))}"
                    ))

                # Checa existência da tabela antes do dry-run
                db_has_truss_table = table_exists(Truss)
                if dry_run and not db_has_truss_table:
                    self.stdout.write(self.style.WARNING(
                        "[import_trusses] Tabela do Truss não existe no DB atual. "
                        "Em dry-run, não consultarei o banco; vou contar todas as linhas como 'criadas'."
                    ))

                ctx = transaction.atomic() if not dry_run else nullcontext()
                with ctx:
                    for idx, row in enumerate(reader, start=2):  # 2 = primeira linha de dados
                        try:
                            # PK
                            try:
                                pk = int(str(row.get("id", "")).strip())
                            except Exception:
                                errors += 1
                                if len(error_lines) < max_error_lines:
                                    error_lines.append(f"Linha {idx}: id inválido ({row.get('id')!r})")
                                continue

                            defaults = {
                                "job_number": (row.get("job_number") or "").strip(),
                                "truss_number": str(row.get("truss_number") or "").strip(),
                                "tipo": (row.get("tipo") or "").strip(),
                                # Se o campo não aceita null, troque para 0 conforme sua regra de negócio:
                                "quantidade": to_int_or_none(row.get("quantidade")),
                                "ply": to_int_or_none(row.get("ply")),
                                "endereco": (row.get("endereco") or "").strip(),
                                "tamanho": (row.get("tamanho") or "").strip(),
                                "status": (row.get("status") or "").strip(),
                            }

                            if dry_run:
                                if db_has_truss_table:
                                    if Truss.objects.filter(pk=pk).exists():
                                        updated += 1
                                    else:
                                        created += 1
                                else:
                                    created += 1
                            else:
                                _, created_flag = Truss.objects.update_or_create(id=pk, defaults=defaults)
                                if created_flag:
                                    created += 1
                                else:
                                    updated += 1

                            if (idx - 1) % 1000 == 0:
                                self.stdout.write(self.style.NOTICE(f"[import_trusses] Processadas {idx-1} linhas..."))

                        except IntegrityError as e:
                            errors += 1
                            if len(error_lines) < max_error_lines:
                                error_lines.append(f"Linha {idx}: IntegrityError: {e}")
                        except Exception as e:
                            errors += 1
                            if len(error_lines) < max_error_lines:
                                error_lines.append(f"Linha {idx}: Erro inesperado: {e}")

        except FileNotFoundError:
            raise CommandError(f"CSV não encontrado: {csv_path}")

        if error_lines:
            self.stdout.write(self.style.WARNING("[import_trusses] Exemplos de erros:"))
            for line in error_lines:
                self.stdout.write(" - " + line)

        self.stdout.write(self.style.SUCCESS(
            f"[import_trusses] Concluído — criados: {created}, atualizados: {updated}, erros: {errors} (dry-run={dry_run})"
        ))


@contextmanager
def nullcontext():
    yield