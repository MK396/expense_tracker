import os
import sys
from pathlib import Path
from django.core.files.storage import default_storage
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import generics, permissions
from django.contrib.auth.models import User
from .serializers import RegisterSerializer

from .models import Expense, Category
from .serializers import ExpenseSerializer, CategorySerializer
from ocr.gemini_processor import analizuj_paragon_gemini

# Dodajemy folder główny do ścieżki, aby Django widziało moduł 'ocr'
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
from ocr.easyocr_processor import analizuj_paragon_dla_api


class ExpenseListCreateView(generics.ListCreateAPIView):
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Każdy użytkownik widzi TYLKO swoje wydatki
        return Expense.objects.filter(user=self.request.user).order_by('-date')

    def get_serializer(self, *args, **kwargs):
        if isinstance(kwargs.get('data', {}), list):
            kwargs['many'] = True
        return super().get_serializer(*args, **kwargs)

    def perform_create(self, serializer):
        # Automatyczne przypisanie zalogowanego użytkownika (również przy liście)
        if isinstance(serializer.validated_data, list):
            serializer.save(user=self.request.user)
        else:
            serializer.save(user=self.request.user)


class CategoryListCreateView(generics.ListCreateAPIView):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Każdy użytkownik widzi TYLKO swoje kategorie
        return Category.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ExpenseDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Blokada edycji/usunięcia cudzego wydatku
        return Expense.objects.filter(user=self.request.user)

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    # Rejestracja musi być publicznie dostępna dla niezalogowanych
    permission_classes = [permissions.AllowAny]

@api_view(['POST'])
@permission_classes([IsAuthenticated])  # Zabezpieczenie skanowania
def scan_receipt(request):
    if 'receipt' not in request.FILES:
        return Response({"error": "Brak pliku na wejściu."}, status=status.HTTP_400_BAD_REQUEST)

    plik = request.FILES['receipt']
    file_name = default_storage.save(f"uploads/{plik.name}", plik)
    file_path = Path(default_storage.path(file_name))

    try:
        produkty = analizuj_paragon_dla_api(file_path)
        return Response({"status": "success", "produkty": produkty}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    finally:
        # Blok finally gwarantuje usunięcie pliku nawet w razie wyjątku
        if os.path.exists(file_path):
            os.remove(file_path)


@api_view(['POST'])
@permission_classes([IsAuthenticated])  # Zabezpieczenie skanowania Gemini
def scan_receipt_gemini(request):
    if 'receipt' not in request.FILES:
        return Response({"error": "Brak pliku na wejściu."}, status=status.HTTP_400_BAD_REQUEST)

    plik = request.FILES['receipt']
    file_name = default_storage.save(f"uploads/{plik.name}", plik)
    file_path = Path(default_storage.path(file_name))

    try:
        produkty = analizuj_paragon_gemini(file_path)
        return Response({"status": "success", "produkty": produkty}, status=status.HTTP_200_OK)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)