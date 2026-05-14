from django.db import models
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Categories"

class Expense(models.Model):
    name = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL,
        null=True, 
        blank=True,
        related_name='expenses'
    )
    date = models.DateField(default=timezone.now)

    def __str__(self):
        cat_name = self.category.name if self.category else "Brak"
        return f"{self.name} - {cat_name}: {self.amount} ({self.date})"