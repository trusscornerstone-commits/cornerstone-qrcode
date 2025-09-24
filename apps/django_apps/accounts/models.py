from django.db import models

class Truss(models.Model):
    # Preserva o ID do CSV/QR como chave primária para bater com /truss/<id>
    id = models.IntegerField(primary_key=True)

    job_number = models.CharField(max_length=100, blank=True, default="")
    truss_number = models.CharField(max_length=100, blank=True, default="")
    tipo = models.CharField(max_length=100, blank=True, default="")
    quantidade = models.IntegerField(null=True, blank=True)
    ply = models.IntegerField(null=True, blank=True)
    endereco = models.CharField(max_length=255, blank=True, default="")
    tamanho = models.CharField(max_length=100, blank=True, default="")
    status = models.CharField(max_length=100, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["job_number"]),
            models.Index(fields=["truss_number"]),
        ]

    def __str__(self):
        return f"{self.truss_number or self.id} ({self.job_number})"