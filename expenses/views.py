from django.shortcuts import render
from rest_framework import generics
from .models import Expense
from .serializers import ExpenseSerializer

# Pobieranie (GET) i dodawanie wydatków (POST)
class ExpenseListCreateView(generics.ListCreateAPIView):
    # definicja jakie dane będą pobierane i jak będą serializowane
    queryset = Expense.objects.all().order_by('-date')
    serializer_class = ExpenseSerializer
