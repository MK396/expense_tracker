from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categories')

    def __str__(self):
        return f"{self.name} ({self.user.username})"
    
    class Meta:
        verbose_name_plural = "Categories"
        constraints = [
            models.UniqueConstraint(fields=['user', 'name'], name='unique_user_category')
        ]

class Expense(models.Model):
    name = models.CharField(max_length=200)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL,
        null=True, 
        blank=True,
        related_name='expenses'
    )
    date = models.DateField(default=timezone.localdate)
    items = models.JSONField(default=list, blank=True, null=True)

    def __str__(self):
        cat_name = self.category.name if self.category else "Brak"
        return f"{self.name} - {cat_name}: {self.amount} ({self.date})"