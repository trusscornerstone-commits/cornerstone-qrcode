# accounts/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import pytz

# Define fuso de Boston
BOSTON_TZ = pytz.timezone("America/New_York")


class Truss(models.Model):
    truss_id = models.CharField(max_length=50)
    serial_number = models.PositiveIntegerField(default=1)
    quantity = models.PositiveIntegerField(default=1)
    span = models.CharField(max_length=20)

    # Campos adicionais
    floor = models.CharField(max_length=50, null=True, blank=True)
    project = models.CharField(max_length=100, null=True, blank=True)
    table_number = models.CharField(max_length=100, null=True, blank=True)

    # Controle de datas e produção
    create_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(auto_now=True)
    produced = models.BooleanField(default=False)
    production_date = models.DateTimeField(null=True, blank=True)
    #produced_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    producer_name = models.CharField(max_length=150, null=True, blank=True)

    @property
    def formatted_create_date(self):
        return self.formatted_datetime(self.create_date)

    @property
    def formatted_update_date(self):
        return self.formatted_datetime(self.update_date)

    @property
    def formatted_production_date(self):
        return self.formatted_datetime(self.production_date)

    class Meta:
        unique_together = ('truss_id', 'serial_number')

    def __str__(self):
        return f"{self.truss_id}-{self.serial_number}/{self.quantity}"

    def save(self, *args, **kwargs):
        """Garante que datas fiquem no fuso de Boston, sem microssegundos, e 'produced' seja boolean."""
        now_boston = timezone.now().astimezone(BOSTON_TZ).replace(microsecond=0)

        if not self.id:  # Novo registro
            self.create_date = now_boston
        self.update_date = now_boston

        # Corrige campo produced (True/False real)
        if isinstance(self.produced, str):
            self.produced = self.produced.lower() in ["true", "1", "t"]

        super().save(*args, **kwargs)

    def check_produced(self, user):
        """Marca a truss como produced uma única vez, com fuso Boston e timestamp limpo."""
        if not self.produced:
            now_boston = timezone.now().astimezone(BOSTON_TZ).replace(microsecond=0)
            self.produced = True
            #self.produced_by = user
            self.producer_name = user.username
            self.production_date = now_boston
            self.update_date = now_boston
            self.save()

    def formatted_datetime(self, dt):
        """Retorna data formatada como MM-DD-YYYY HH:MM:SS no fuso Boston."""
        if not dt:
            return ""
        dt_boston = dt.astimezone(BOSTON_TZ).replace(microsecond=0)
        return dt_boston.strftime("%m-%d-%Y %H:%M:%S")
