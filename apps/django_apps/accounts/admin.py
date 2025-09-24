from django.contrib import admin
from .models import Truss


@admin.register(Truss)
class TrussAdmin(admin.ModelAdmin):
    list_display = ("id", "truss_number", "job_number", "tipo", "quantidade", "status", "updated_at")
    list_display_links = ("id", "truss_number")
    search_fields = ("id", "truss_number", "job_number", "endereco")
    list_filter = ("status", "tipo")
    ordering = ("-updated_at", "id")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("Identificação", {
            "fields": ("id", "job_number", "truss_number"),
        }),
        ("Especificações", {
            "fields": ("tipo", "quantidade", "ply", "tamanho", "status"),
        }),
        ("Localização", {
            "fields": ("endereco",),
        }),
        ("Metadados", {
            "fields": ("created_at", "updated_at"),
        }),
    )
    list_per_page = 50
    save_on_top = True