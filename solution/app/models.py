from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator

User = get_user_model()

class DataStore(models.Model):
    owner       = models.ForeignKey(User, on_delete=models.CASCADE)
    csv         = models.FileField(upload_to='documents')
    uploaded_at = models.DateTimeField(auto_now=True)

    class Meta:
       unique_together = ("owner", "csv")
    
    def __str__(self):
        return self.csv.name

class GameSale(models.Model):
    metadata     = models.ForeignKey(DataStore, on_delete=models.CASCADE)
    rank         = models.PositiveIntegerField()
    name         = models.CharField(max_length=255)
    platform     = models.CharField(max_length=255)
    year         = models.PositiveIntegerField(validators=[MinValueValidator(1000), MaxValueValidator(9999)])
    genre        = models.CharField(max_length=255)
    publisher    = models.CharField(max_length=255)
    na_sales     = models.FloatField(validators=[MinValueValidator(0.0)])
    eu_sales     = models.FloatField(validators=[MinValueValidator(0.0)])
    jp_sales     = models.FloatField(validators=[MinValueValidator(0.0)])
    other_sales  = models.FloatField(validators=[MinValueValidator(0.0)])
    global_sales = models.FloatField(validators=[MinValueValidator(0.0)])

    def __str__(self):
        return self.name