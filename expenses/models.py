from django.db import models

# Create your models here.

class Expense(models.Model):
    name = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=100, default='Other')
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.amount}"
