# accounts/models.py
from django.db import models
from django.utils import timezone
import pytz

# Fuso horário de Boston
BOSTON_TZ = pytz.timezone("America/New_York")


class QrCodeTruss(models.Model):
    """Modelo vinculado à tabela qr_codetrusses (novo padrão de QR Code)."""
    truss_id = models.CharField(max_length=50)
    unit_number = models.PositiveIntegerField(default=1)
    quantity = models.PositiveIntegerField(default=1)
    span = models.CharField(max_length=20, blank=True, null=True)
    project = models.CharField(max_length=100, blank=True, null=True)
    floor = models.CharField(max_length=50, blank=True, null=True)

    create_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(auto_now=True)
    produced = models.BooleanField(default=False)
    production_date = models.DateTimeField(null=True, blank=True)
    producer_name = models.CharField(max_length=150, null=True, blank=True)

    class Meta:
        db_table = "qr_codetrusses"
        managed = False
        unique_together = ("truss_id", "unit_number", "floor")

    def __str__(self):
        return f"{self.truss_id} ({self.unit_number}/{self.quantity}) [{self.floor}]"

    def save(self, *args, **kwargs):
        """
        Salva datas usando timezone correto (America/New_York em settings)
        O Django converte automaticamente para UTC ao salvar.
        """
        now = timezone.now().replace(microsecond=0)

        if not self.id:
            self.create_date = now

        self.update_date = now

        if isinstance(self.produced, str):
            self.produced = self.produced.lower() in ["true", "1", "t", "yes"]

        super().save(*args, **kwargs)

    def check_produced(self, user):
        """Marca a truss como produzida uma única vez."""
        if not self.produced:
            now = timezone.now().replace(microsecond=0)
            self.produced = True
            self.producer_name = user.username
            self.production_date = now
            self.update_date = now
            self.save()

    # --------------------------
    # Datas formatadas
    # --------------------------
    @property
    def formatted_create_date(self):
        return self._format_datetime(self.create_date)

    @property
    def formatted_update_date(self):
        return self._format_datetime(self.update_date)

    @property
    def formatted_production_date(self):
        return self._format_datetime(self.production_date)

    def _format_datetime(self, dt):
        """Formata data no padrão MM-DD-YYYY HH:MM:SS (Boston)."""
        if not dt:
            return ""
        dt_boston = dt.astimezone(BOSTON_TZ).replace(microsecond=0)
        return dt_boston.strftime("%m-%d-%Y %H:%M:%S")
