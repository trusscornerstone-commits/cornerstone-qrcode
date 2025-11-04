from django.contrib import admin
from django.core.exceptions import FieldDoesNotExist
from .models import Truss
import pytz

# Define o fuso horário de Boston
BOSTON_TZ = pytz.timezone("America/New_York")


def has_field(model, name: str) -> bool:
    """Verifica se o campo existe no modelo"""
    try:
        model._meta.get_field(name)
        return True
    except FieldDoesNotExist:
        return False
    except Exception:
        return False


# Configurações dinâmicas baseadas nos campos do modelo
LIST_DISPLAY = ["id", "truss_id", "serial_number", "span", "quantity", "produced"]
if has_field(Truss, "producer_name"):
    LIST_DISPLAY.append("producer_name")
LIST_DISPLAY += ["formatted_production_date", "formatted_create_date", "formatted_update_date"]

ORDERING = ["-update_date", "id"]
READONLY_FIELDS = []
for f in ("create_date", "update_date"):
    if has_field(Truss, f):
        READONLY_FIELDS.append(f)

LIST_FILTER = ("produced", "truss_id")
SEARCH_FIELDS = ("truss_id", "serial_number", "span")


@admin.register(Truss)
class TrussAdmin(admin.ModelAdmin):
    list_display = LIST_DISPLAY
    list_filter = LIST_FILTER
    search_fields = SEARCH_FIELDS
    readonly_fields = READONLY_FIELDS
    ordering = ORDERING

    # 🔹 Utilitário interno para formatar datas no fuso de Boston
    def _format_datetime(self, dt):
        if not dt:
            return ""
        dt_boston = dt.astimezone(BOSTON_TZ).replace(microsecond=0)
        return dt_boston.strftime("%m-%d-%Y %H:%M:%S")

    # 🔹 Exibição formatada no admin
    def formatted_create_date(self, obj):
        return self._format_datetime(obj.create_date)
    formatted_create_date.short_description = "Created"

    def formatted_update_date(self, obj):
        return self._format_datetime(obj.update_date)
    formatted_update_date.short_description = "Last Updated"

    def formatted_production_date(self, obj):
        return self._format_datetime(obj.production_date)
    formatted_production_date.short_description = "Produced At"
