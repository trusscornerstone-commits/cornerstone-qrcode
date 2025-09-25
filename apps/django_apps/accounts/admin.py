from django.contrib import admin
from django.core.exceptions import FieldDoesNotExist
from .models import Truss


def has_field(model, name: str) -> bool:
    try:
        model._meta.get_field(name)
        return True
    except FieldDoesNotExist:
        return False
    except Exception:
        return False


# list_display dinâmico (usa updated_at se existir)
LIST_DISPLAY = ["id", "truss_number", "job_number"]
for f in ("tipo", "quantidade", "status"):
    if has_field(Truss, f):
        LIST_DISPLAY.append(f)
if has_field(Truss, "updated_at"):
    LIST_DISPLAY.append("updated_at")

# ordering dinâmico (prioriza -updated_at se existir)
ORDERING = []
if has_field(Truss, "updated_at"):
    ORDERING.append("-updated_at")
ORDERING.append("id")

# readonly_fields dinâmico (created_at/updated_at se existirem)
READONLY_FIELDS = []
for f in ("created_at", "updated_at"):
    if has_field(Truss, f):
        READONLY_FIELDS.append(f)

# fieldsets dinâmicos
identificacao_fields = ["id", "job_number", "truss_number"]

especificacoes_fields = []
for f in ("tipo", "quantidade", "ply", "tamanho", "status"):
    if has_field(Truss, f):
        especificacoes_fields.append(f)

localizacao_fields = []
if has_field(Truss, "endereco"):
    localizacao_fields.append("endereco")

metadados_fields = []
for f in ("created_at", "updated_at"):
    if has_field(Truss, f):
        metadados_fields.append(f)

FIELDSETS = [
    ("Identificação", {"fields": tuple(identificacao_fields)}),
    ("Especificações", {"fields": tuple(especificacoes_fields)}),
]
if localizacao_fields:
    FIELDSETS.append(("Localização", {"fields": tuple(localizacao_fields)}))
if metadados_fields:
    FIELDSETS.append(("Metadados", {"fields": tuple(metadados_fields)}))


# list_filter e search_fields apenas com campos existentes
LIST_FILTER = tuple(f for f in ("status", "tipo") if has_field(Truss, f))
SEARCH_FIELDS = ["id", "truss_number", "job_number"]
if has_field(Truss, "endereco"):
    SEARCH_FIELDS.append("endereco")


@admin.register(Truss)
class TrussAdmin(admin.ModelAdmin):
    list_display = tuple(LIST_DISPLAY)
    list_display_links = ("id", "truss_number")
    search_fields = tuple(SEARCH_FIELDS)
    list_filter = LIST_FILTER
    ordering = tuple(ORDERING)
    readonly_fields = tuple(READONLY_FIELDS)
    fieldsets = tuple(FIELDSETS)
    list_per_page = 50
    save_on_top = True