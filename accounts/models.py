from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Truss(models.Model):
    truss_id = models.CharField(max_length=50)
    quantidade = models.IntegerField(default=1)
    span = models.CharField(max_length=50)
    produzida = models.BooleanField(default=False)
    produzido_por = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    data_producao = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.truss_id
