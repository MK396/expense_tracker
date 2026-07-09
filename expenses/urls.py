from django.urls import path
from .views import ExpenseListCreateView, CategoryListCreateView, scan_receipt, scan_receipt_gemini

urlpatterns = [
    path('expenses/', ExpenseListCreateView.as_view(), name='expense-list'),
    path('categories/', CategoryListCreateView.as_view(), name='category-list'),
    path('scan/', scan_receipt, name='scan-receipt'), # NOWA LINIJKA
    path('scan-gemini/', scan_receipt_gemini, name='scan-receipt-gemini'),
]