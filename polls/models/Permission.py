from django.db import models

class Permission(models.Model):
    ten_quyen = models.CharField(max_length=100, unique=True)
    mo_ta = models.TextField(blank=True)
    code = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.ten_quyen 