from django.urls import path
from .views import ExpenseListCreateView, CategoryListCreateView

urlpatterns = [
    path('expenses/', ExpenseListCreateView.as_view(), name='expense-list'),
    path('categories/', CategoryListCreateView.as_view(), name='category-list'),

]