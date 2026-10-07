from rest_framework import serializers
from .models import Expense, Category
from django.contrib.auth.models import User

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


class ExpenseSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(
        slug_field='name',
        queryset=Category.objects.none()  # Domyślnie puste, ustawiane dynamicznie w __init__
    )

    class Meta:
        model = Expense
        fields = ['id', 'name', 'amount', 'category', 'date', 'items']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pobieramy obiekt żądania (request) z kontekstu serializera
        request = self.context.get('request', None)
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            # Ograniczamy wybór kategorii wyłącznie do kategorii zalogowanego użytkownika
            self.fields['category'].queryset = Category.objects.filter(user=request.user)

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['username', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password']
        )
        # Tworzenie zestawu podstawowych kategorii
        default_categories = ['Jedzenie', 'Transport', 'Dom', 'Rozrywka']
        Category.objects.bulk_create([
            Category(name=cat_name, user=user) for cat_name in default_categories
        ])
        return user