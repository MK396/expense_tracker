from django.urls import path
from .views import ExpenseListCreateView, ExpenseDetailView,CategoryListCreateView, scan_receipt, scan_receipt_gemini, RegisterView

urlpatterns = [
    path('expenses/', ExpenseListCreateView.as_view(), name='expense-list'),
    path('expenses/<int:pk>/', ExpenseDetailView.as_view(), name='expense-detail'),
    path('categories/', CategoryListCreateView.as_view(), name='category-list'),
    path('scan/', scan_receipt, name='scan-receipt'), # NOWA LINIJKA
    path('scan-gemini/', scan_receipt_gemini, name='scan-receipt-gemini'),
    path('register/', RegisterView.as_view(), name='register'),
]