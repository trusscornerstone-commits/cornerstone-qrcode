import csv
import re
from contextlib import contextmanager
from typing import Dict, List, Optional

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, connection
from django.db.utils import IntegrityError

# Ajuste se o modelo estiver em outro local
from apps.django_apps.accounts.models import Truss


def normalize_col(name: str) -> str:
    """
    Normaliza o nome da coluna:
    - lower
    - troca caracteres não alfanuméricos por '_'
    - remove '_' duplicados
    """
    n = re.sub(r'[^0-9a-zA-Z]+', '_', name.strip().lower())
    n = re.sub(r'_+', '_', n).strip('_')
    return n


@contextmanager
def nullcontext():
    yield


class Command(BaseCommand):
    help = "Importa/atualiza Truss a partir de um CSV no NOVO formato de cabeçalho."

    def add_arguments(self, parser):
        parser.add_argument("--csv", dest="csv_path", required=True, help="Caminho do arquivo CSV")
        parser.add_argument("--delimiter", dest="delimiter", default=",", help="Delimitador (padrão: ,)")
        parser.add_argument("--dry-run", action="store_true", help="Mostra contagem sem gravar no banco")

    def handle(self, *args, **opts):
        csv_path = opts["csv_path"]
        delimiter = opts["delimiter"]
        dry_run = bool(opts.get("dry_run"))

        created, updated, errors = 0, 0, 0
        error_lines: List[str] = []
        max_error_lines = 20

        self.stdout.write(self.style.NOTICE(f"[import_trusses] Lendo {csv_path} ... (dry-run={dry_run})"))

        # Aliases: coluna normalizada → campo do modelo
        # Para cada campo do modelo definimos os possíveis nomes (normalizados) das colunas de origem
        alias_map = {
            "id": ["id"],
            "truss_number": ["truss_number", "truss_num", "trussnumber"],
            "tipo": ["truss_type", "type"],
            "quantidade": ["qnty", "qty", "quantity"],
            "ply": ["ply"],
            # Job_Reference está sendo usado como endereço nesta nova planilha
            "endereco": ["job_reference", "address", "endereco", "location"],
            # 'Size (ft)' -> tamanho
            "tamanho": ["size_ft", "size", "size_ft_", "size_ft__",
                        "size_ft__", "size_ft___", "size_ft____", "size_ft_____", "size_ft______", "size_ft_______",
                        "size_ft________", "size", "size_ft", "size_ft_", "size_ft__", "size_ft___", "size_ft____",
                        "size_ft_____", "size_ft______", "size_ft_______", "size_ft________", "size_ft_________",
                        "size_ft__________", "size_ft___________", "size_ft____________", "size_ft_____________",
                        "size_ft______________", "size_ft_______________", "size_ft________________"],
            # Normalizado de "Size (ft)" vira "size_ft"
            "status": ["status"],
            # Campos do modelo que podem ficar vazios se ausentes
            "job_number": ["job_number", "job", "job_ref", "jobreference"],  # no CSV novo não veio; ficará ""
        }

        # Campos obrigatórios mínimos para processar
        required_alias_targets = {"id", "truss_number"}

        def build_reverse_lookup(fieldnames) -> Dict[str, str]:
            """
            Retorna dict: nome_do_campo_modelo -> nome_da_coluna_original (primeiro alias que encontrar)
            """
            normalized_mapping = {normalize_col(c): c for c in fieldnames}
            result = {}
            for model_field, aliases in alias_map.items():
                for a in aliases:
                    if a in normalized_mapping:
                        result[model_field] = normalized_mapping[a]
                        break
            return result

        def to_int_or_none(value: Optional[str]):
            if value is None:
                return None
            s = str(value).strip()
            if s == "":
                return None
            # só aceita inteiro puro
            if re.fullmatch(r"-?\d+", s):
                try:
                    return int(s)
                except Exception:
                    return None
            return None

        def to_decimal_or_str(value: Optional[str]):
            if value is None:
                return ""
            s = str(value).strip()
            if s == "":
                return ""
            # deixe como está; se o campo for DecimalField o Django converte; se for Integer, trate
            return s

        def table_exists(model) -> bool:
            try:
                with connection.cursor():
                    tables = set(connection.introspection.table_names())
                return model._meta.db_table in tables
            except Exception:
                return False

        try:
            with open(csv_path, newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f, delimiter=delimiter)

                if not reader.fieldnames:
                    raise CommandError("Cabeçalho não encontrado no CSV.")

                reverse_lookup = build_reverse_lookup(reader.fieldnames)

                missing_required = [mf for mf in required_alias_targets if mf not in reverse_lookup]
                if missing_required:
                    raise CommandError(
                        f"Colunas obrigatórias ausentes (considerando aliases): {', '.join(missing_required)}"
                    )

                db_has_table = table_exists(Truss)
                if dry_run and not db_has_table:
                    self.stdout.write(self.style.WARNING(
                        "[import_trusses] Tabela inexistente — em dry-run apenas contarei como 'criadas'."
                    ))

                ctx = transaction.atomic() if not dry_run else nullcontext()
                with ctx:
                    for idx, row in enumerate(reader, start=2):
                        try:
                            try:
                                raw_id = row[reverse_lookup["id"]]
                                pk = int(str(raw_id).strip())
                            except Exception:
                                errors += 1
                                if len(error_lines) < max_error_lines:
                                    error_lines.append(f"Linha {idx}: id inválido ({row.get(reverse_lookup.get('id', 'id'))!r})")
                                continue

                            # Monta defaults baseado no que foi encontrado
                            # Se um campo não existir na planilha, cai para "" / None
                            def get(model_field, transform=lambda x: x, default=""):
                                col = reverse_lookup.get(model_field)
                                if not col:
                                    return default
                                return transform(row.get(col))

                            defaults = {
                                "truss_number": get("truss_number", lambda v: (v or "").strip(), ""),
                                "tipo": get("tipo", lambda v: (v or "").strip(), ""),
                                "quantidade": get("quantidade", to_int_or_none, None),
                                "ply": get("ply", to_decimal_or_str, ""),
                                # Job_Reference -> endereco
                                "endereco": get("endereco", lambda v: (v or "").strip(), ""),
                                # "Size (ft)" -> tamanho (mantemos string; se quiser número: str(int(float(...))))
                                "tamanho": get("tamanho", lambda v: str(v).strip(), ""),
                                "status": get("status", lambda v: (v or "").strip(), ""),
                                "job_number": get("job_number", lambda v: (v or "").strip(), ""),
                            }

                            if dry_run:
                                if db_has_table:
                                    if Truss.objects.filter(pk=pk).exists():
                                        updated += 1
                                    else:
                                        created += 1
                                else:
                                    created += 1
                            else:
                                obj, created_flag = Truss.objects.update_or_create(
                                    id=pk,
                                    defaults=defaults,
                                )
                                if created_flag:
                                    created += 1
                                else:
                                    updated += 1

                            if (idx - 1) % 1000 == 0:
                                self.stdout.write(self.style.NOTICE(f"[import_trusses] {idx-1} linhas processadas..."))

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