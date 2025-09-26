from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from apps.django_apps.accounts.models import Truss

from apps.qrcode_app.services.labels import (
    gerar_de_queryset,
)

class Command(BaseCommand):
    help = "Gera etiquetas/QR Codes dos Trusses direto do banco."

    def add_arguments(self, parser):
        parser.add_argument("--output-dir", default="apps/qrcode_app/templates/qrcodes")
        parser.add_argument("--json-dir", default="apps/qrcode_app/static/truss-data")
        parser.add_argument("--logo-path", default="cornerstone_logo.png")
        parser.add_argument("--web-base-url", default=None, help="Override de WEB_BASE_URL")
        parser.add_argument("--empresa-endereco", default="Rua Exemplo, 123 - Cidade/UF")
        parser.add_argument("--empresa-tel", default="(11) 99999-8888")
        parser.add_argument("--pdf-name", default="labels.pdf")
        parser.add_argument("--ids", help="Filtra IDs ex: 1,2,3")
        parser.add_argument("--job-number")
        parser.add_argument("--status")
        parser.add_argument("--tipo")
        parser.add_argument("--limit", type=int)
        parser.add_argument("--no-json", action="store_true", help="Não exportar JSONs")
        parser.add_argument("--no-clean", action="store_true", help="Não limpar arquivos antigos")
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **opts):
        base_dir = Path(settings.BASE_DIR)
        output_dir = base_dir / opts["output_dir"]
        json_dir = base_dir / opts["json_dir"]
        logo_path = base_dir / opts["logo_path"]

        if not logo_path.exists():
            raise CommandError(f"Logo não encontrado: {logo_path}")

        web_base = opts["web_base_url"] or settings.__dict__.get("WEB_BASE_URL") or \
            settings.CONFIG.get("WEB_BASE_URL") if hasattr(settings, "CONFIG") else None
        if not web_base:
            web_base = "https://cornerstone-app.onrender.com/truss"

        qs = Truss.objects.all().order_by("id")

        if opts.get("ids"):
            try:
                id_list = [int(x.strip()) for x in opts["ids"].split(",") if x.strip()]
                qs = qs.filter(id__in=id_list)
            except ValueError:
                raise CommandError("--ids inválido. Use inteiros separados por vírgula.")

        if opts.get("job_number"):
            qs = qs.filter(job_number=opts["job_number"])
        if opts.get("status"):
            qs = qs.filter(status=opts["status"])
        if opts.get("tipo"):
            qs = qs.filter(tipo=opts["tipo"])
        if opts.get("limit"):
            qs = qs[: opts["limit"]]

        count = qs.count()
        self.stdout.write(self.style.NOTICE(
            f"[generate_truss_labels] Selecionados {count} trusses. WEB_BASE_URL={web_base}"
        ))

        if opts["dry_run"]:
            total_labels = 0
            for t in qs:
                q = t.quantidade if t.quantidade and t.quantidade > 0 else 1
                total_labels += q
            self.stdout.write(self.style.SUCCESS(
                f"[generate_truss_labels] DRY-RUN: geraria {total_labels} etiquetas."
            ))
            return

        trusses_count, imgs_count, pdf_path = gerar_de_queryset(
            qs,
            output_dir=output_dir,
            json_dir=json_dir,
            base_url=web_base,
            empresa_endereco=opts["empresa_endereco"],
            empresa_tel=opts["empresa_tel"],
            logo_path=logo_path,
            pdf_name=opts["pdf_name"],
            clean=not opts["no_clean"],
            export_json=not opts["no_json"],
        )

        self.stdout.write(self.style.SUCCESS(
            f"[generate_truss_labels] Concluído: {imgs_count} imagens para {trusses_count} trusses. PDF={pdf_path}"
        ))