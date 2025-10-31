# accounts/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Truss(models.Model):
    truss_id = models.CharField(max_length=50)  # Ex: T20A
    serial_number = models.PositiveIntegerField(default=1)  # Ex: 1 de 3
    quantidade = models.PositiveIntegerField(default=1)  # Total de peças (ex: 3)
    span = models.CharField(max_length=20)
    produzida = models.BooleanField(default=False)
    data_producao = models.DateTimeField(null=True, blank=True)
    produzido_por = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        unique_together = ('truss_id', 'serial_number')  # Evita duplicatas

    def __str__(self):
        return f"{self.truss_id}-{self.serial_number}/{self.quantidade}"

    def marcar_produzida(self, user):
        """Marca a truss como produzida uma única vez"""
        if not self.produzida:
            self.produzida = True
            self.produzido_por = user
            self.data_producao = timezone.now()
            self.save()
