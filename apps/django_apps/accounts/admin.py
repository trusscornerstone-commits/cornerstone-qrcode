from django.contrib import admin
from .models import Truss

@admin.register(Truss)
class TrussAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "name", "created_at")
    search_fields = ("code", "name")
    ordering = ("-created_at",)