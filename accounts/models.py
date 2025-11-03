# accounts/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Truss(models.Model):
    truss_id = models.CharField(max_length=50)
    serial_number = models.PositiveIntegerField(default=1)
    quantidade = models.PositiveIntegerField(default=1)
    span = models.CharField(max_length=20)

    # Novos campos adicionais
    floor = models.CharField(max_length=50, null=True, blank=True)
    project = models.CharField(max_length=100, null=True, blank=True)
    table_name = models.CharField(max_length=100, null=True, blank=True)

    # Controle de data e produção
    create_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(auto_now=True)
    produzida = models.BooleanField(default=False)
    data_producao = models.DateTimeField(null=True, blank=True)
    produzido_por = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        unique_together = ('truss_id', 'serial_number')

    def __str__(self):
        return f"{self.truss_id}-{self.serial_number}/{self.quantidade}"

    def marcar_produzida(self, user):
        """Marca a truss como produzida uma única vez"""
        if not self.produzida:
            self.produzida = True
            self.produzido_por = user
            self.data_producao = timezone.now()
            self.update_date = timezone.now()
            self.save()
