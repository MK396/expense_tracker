import os
import math
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.storage import default_storage
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.throttling import SimpleRateThrottle

from rest_framework.decorators import api_view, permission_classes, throttle_classes

from axes.models import AccessAttempt
from axes.helpers import get_client_ip_address
from axes.utils import reset

from .models import Category, Expense
from .serializers import (
    CategorySerializer,
    ExpenseSerializer,
    RegisterSerializer,
)


# ==========================================
# UWIERZYTELNIANIE Z CIASTECZKAMI (HttpOnly) & AXES
# ==========================================

class CookieTokenObtainPairView(TokenObtainPairView):
    """
    Logowanie: Zwraca access_token w JSON, refresh w HttpOnly,
    resetuje próby po udanym logowaniu i raportuje stan blokad.
    """
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)

            # --- RESETOWANIE LICZNIKA AXES PO UDANYM LOGOWANIU ---
            ip = get_client_ip_address(request)
            username = request.data.get('username')
            reset(ip=ip, username=username)

            response = Response(serializer.validated_data, status=status.HTTP_200_OK)
            refresh_token = response.data.pop('refresh', None)
            if refresh_token:
                response.set_cookie(
                    key='refresh_token',
                    value=refresh_token,
                    httponly=True,
                    secure=not settings.DEBUG,
                    samesite='Lax',
                    path='/api/token/refresh/',
                    max_age=7 * 24 * 3600
                )
            return response

        except Exception:
            ip = get_client_ip_address(request)
            username = request.data.get('username')

            limit = getattr(settings, 'AXES_FAILURE_LIMIT', 5)
            cooloff_hours = getattr(settings, 'AXES_COOLOFF_TIME', 0.25)
            cooloff_seconds = cooloff_hours * 3600

            attempt = AccessAttempt.objects.filter(ip_address=ip, username=username).first()
            if not attempt:
                attempt = AccessAttempt.objects.filter(ip_address=ip).first()

            if attempt:
                elapsed = (timezone.now() - attempt.attempt_time).total_seconds()

                if attempt.failures_since_start >= limit and elapsed < cooloff_seconds:
                    remaining_minutes = math.ceil((cooloff_seconds - elapsed) / 60)
                    return Response({
                        "detail": f"Zbyt wiele prób logowania. Konto zablokowane na {remaining_minutes} min.",
                        "is_locked": True,
                        "remaining_minutes": remaining_minutes
                    }, status=status.HTTP_429_TOO_MANY_REQUESTS)

                remaining_attempts = max(0, limit - attempt.failures_since_start)
                return Response({
                    "detail": f"Niepoprawny login lub hasło. Pozostało prób: {remaining_attempts}.",
                    "is_locked": False,
                    "remaining_attempts": remaining_attempts
                }, status=status.HTTP_401_UNAUTHORIZED)

            return Response({
                "detail": f"Niepoprawny login lub hasło. Pozostało prób: {limit - 1}.",
                "is_locked": False,
                "remaining_attempts": limit - 1
            }, status=status.HTTP_401_UNAUTHORIZED)


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

class ReceiptScanThrottle(SimpleRateThrottle):
    """Limit skanów EasyOCR — po IP (gość) lub user id (zalogowany)."""
    scope = 'receipt_scan'

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        return self.cache_format % {'scope': self.scope, 'ident': ident}


class ReceiptScanGeminiThrottle(SimpleRateThrottle):
    """Limit skanów Gemini — po IP (gość) lub user id (zalogowany)."""
    scope = 'receipt_scan_gemini'

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        return self.cache_format % {'scope': self.scope, 'ident': ident}


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([ReceiptScanThrottle])
def scan_receipt(request):
    from ocr.easyocr_processor import analizuj_paragon_dla_api
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
@permission_classes([AllowAny])
@throttle_classes([ReceiptScanGeminiThrottle])
def scan_receipt_gemini(request):
    from ocr.gemini_processor import analizuj_paragon_gemini
    if 'receipt' not in request.FILES:
        return Response({"error": "Brak pliku na wejściu."}, status=status.HTTP_400_BAD_REQUEST)

    plik = request.FILES['receipt']
    file_name = default_storage.save(f"uploads/{plik.name}", plik)
    file_path = Path(default_storage.path(file_name))

    try:
        produkty = analizuj_paragon_gemini(file_path)
        model = produkty.pop("_model", None)
        return Response(
            {"status": "success", "produkty": produkty, "model": model},
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)