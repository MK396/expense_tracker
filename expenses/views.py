import os
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.storage import default_storage
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from ocr.easyocr_processor import analizuj_paragon_dla_api
from ocr.gemini_processor import analizuj_paragon_gemini

from .models import Category, Expense
from .serializers import (
    CategorySerializer,
    ExpenseSerializer,
    RegisterSerializer,
)


# ==========================================
# UWIERZYTELNIANIE Z CIASTECZKAMI (HttpOnly)
# ==========================================

class CookieTokenObtainPairView(TokenObtainPairView):
    """
    Logowanie: Zwraca access_token w JSON, a refresh_token umieszcza
    w bezpiecznym ciasteczku HttpOnly niedostępnym dla skryptów JS.
    """
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            refresh_token = response.data.pop('refresh', None)
            if refresh_token:
                response.set_cookie(
                    key='refresh_token',
                    value=refresh_token,
                    httponly=True,
                    secure=not settings.DEBUG,  # Wymusza HTTPS na produkcji
                    samesite='Lax',
                    path='/api/token/refresh/',  # Wysyłane wyłącznie do endpointu odświeżania
                    max_age=7 * 24 * 3600       # 7 dni
                )
        return response


class CookieTokenRefreshView(TokenRefreshView):
    """
    Odświeżanie sesji: Odczytuje refresh_token bezpośrednio z ciasteczka HttpOnly.
    """
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')
        if refresh_token:
            data = request.data.copy() if hasattr(request.data, 'copy') else {}
            data['refresh'] = refresh_token
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            return Response(serializer.validated_data, status=status.HTTP_200_OK)

        return super().post(request, *args, **kwargs)


class CookieLogoutView(APIView):
    """
    Wylogowanie: Usuwa ciasteczko z przeglądarki użytkownika.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        response = Response({"detail": "Wylogowano pomyślnie."}, status=status.HTTP_200_OK)
        response.delete_cookie('refresh_token', path='/api/token/refresh/')
        return response


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

# ==========================================
# ZARZĄDZANIE WYDATKAMI I KATEGORIAMI
# ==========================================

class ExpenseListCreateView(generics.ListCreateAPIView):
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Expense.objects.filter(user=self.request.user).order_by('-date')

    def get_serializer(self, *args, **kwargs):
        if isinstance(kwargs.get('data', {}), list):
            kwargs['many'] = True
        return super().get_serializer(*args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CategoryListCreateView(generics.ListCreateAPIView):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ExpenseDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Expense.objects.filter(user=self.request.user)


# ==========================================
# ENDPOINTY SKANOWANIA PARAGONÓW (OCR)
# ==========================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
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
        if os.path.exists(file_path):
            os.remove(file_path)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
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
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)