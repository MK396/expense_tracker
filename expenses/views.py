import os
import sys
from pathlib import Path
from django.core.files.storage import default_storage
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from ocr.gemini_processor import analizuj_paragon_gemini

from .models import Expense, Category
from .serializers import ExpenseSerializer, CategorySerializer

# Dodajemy folder główny do ścieżki, aby Django widziało moduł 'ocr'
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
from ocr.easyocr_processor import analizuj_paragon_dla_api

class ExpenseListCreateView(generics.ListCreateAPIView):
    queryset = Expense.objects.all().order_by('-date')
    serializer_class = ExpenseSerializer

    # Nadpisanie metody pozwala na wysłanie tablicy JSON i zapisanie wielu wydatków naraz
    def get_serializer(self, *args, **kwargs):
        if isinstance(kwargs.get('data', {}), list):
            kwargs['many'] = True
        return super().get_serializer(*args, **kwargs)

class CategoryListCreateView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

@api_view(['POST'])
def scan_receipt(request):
    if 'receipt' not in request.FILES:
        return Response({"error": "Brak pliku na wejściu."}, status=status.HTTP_400_BAD_REQUEST)

    plik = request.FILES['receipt']
    
    # Zapisz plik tymczasowo
    # Zapisz plik tymczasowo
    file_name = default_storage.save(f"uploads/{plik.name}", plik)
    
    # TUTAJ JEST MAGIA: Zamieniamy tekstowy string na obiekt Path
    file_path = Path(default_storage.path(file_name))

    try:
        # Analiza paragonu
        produkty = analizuj_paragon_dla_api(file_path)
        
        # Sprzątanie po analizie
        if os.path.exists(file_path):
            os.remove(file_path)
            
        return Response({"status": "success", "produkty": produkty}, status=status.HTTP_200_OK)
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@api_view(['POST'])
def scan_receipt_gemini(request):
    if 'receipt' not in request.FILES:
        return Response({"error": "Brak pliku na wejściu."}, status=status.HTTP_400_BAD_REQUEST)

    plik = request.FILES['receipt']
    file_name = default_storage.save(f"uploads/{plik.name}", plik)
    file_path = Path(default_storage.path(file_name))

    try:
        # Używamy najnowszego modelu od Google!
        produkty = analizuj_paragon_gemini(file_path)
        
        if os.path.exists(file_path):
            os.remove(file_path)
            
        return Response({"status": "success", "produkty": produkty}, status=status.HTTP_200_OK)
    except Exception as e:
        print("--- PEŁNY BŁĄD GEMINI ---")
        import traceback
        traceback.print_exc()
        if os.path.exists(file_path):
            os.remove(file_path)
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)