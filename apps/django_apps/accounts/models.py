from django.db import models

class Truss(models.Model):
    id = models.IntegerField(primary_key=True)  # preserva ID do CSV
    job_number = models.CharField(max_length=50, blank=True, default="")
    truss_number = models.CharField(max_length=50, blank=True, default="")
    tipo = models.CharField(max_length=50, blank=True, default="")
    quantidade = models.IntegerField(null=True, blank=True)
    # Seu CSV tem decimais (ex.: 1.2); use DecimalField ou FloatField
    ply = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    endereco = models.CharField(max_length=255, blank=True, default="")
    tamanho = models.CharField(max_length=50, blank=True, default="")
    status = models.CharField(max_length=50, blank=True, default="")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Truss"
        verbose_name_plural = "Trusses"
        ordering = ("-updated_at", "-id")

    def __str__(self):
        return f"{self.truss_number} ({self.job_number})"