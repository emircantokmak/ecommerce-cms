from django.contrib.auth.models import User
from decimal import Decimal
from rest_framework import serializers
from .models import Cart, CartItem, Category, Favorite, Product , ProductImage


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ["id", "username", "email"]


class UserProfileUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ["username", "email"]

    def validate_username(self, value):
        user = self.instance

        if User.objects.filter(
            username__iexact=value
        ).exclude(
            pk=user.pk
        ).exists():
            raise serializers.ValidationError(
                "Bu kullanıcı adı zaten kullanılıyor."
            )

        return value

    def validate_email(self, value):
        user = self.instance

        if value and User.objects.filter(
            email__iexact=value
        ).exclude(
            pk=user.pk
        ).exists():
            raise serializers.ValidationError(
                "Bu e-posta adresi zaten kullanılıyor."
            )

        return value


class RegisterSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        write_only=True,
        min_length=6
    )
    email = serializers.EmailField(required=True)
    class Meta:
        model = User
        fields = ["username", "email", "password"]

    def validate_password(self, value):
        from django.contrib.auth.password_validation import validate_password
        validate_password(value)
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            is_active=False
        )

        return user
    def validate_username(self,value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("Bu kullanıcı adı zaten kullanılıyor.")
        return value
    def validate_email(self,value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Bu e-mail zaten kullanılıyor.")
        return value
        
            
    
# PRODUCT

class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "slug",
            "created_at"
        ]


# IMAGE


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = [
            "id",
            "image",
            "is_main",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
        ]

    def create(self, validated_data):
        product = self.context["product"]

        if validated_data.get("is_main", False):
            ProductImage.objects.filter(
                product=product
            ).update(is_main=False)

        return ProductImage.objects.create(
            product=product,
            **validated_data,
        )

    def update(self, instance, validated_data):
        if validated_data.get("is_main", False):
            ProductImage.objects.filter(
                product=instance.product
            ).exclude(
                id=instance.id
            ).update(is_main=False)

        return super().update(instance, validated_data)


class ProductSerializer(serializers.ModelSerializer):

    price = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.01"),
    )
    user = serializers.ReadOnlyField(source="user.username")
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "user",
            "category",
            "title",
            "description",
            "price",
            "stock",
            "created_at",
            "updated_at",
            "is_active",
            "is_featured",
            "images"
        ]

        read_only_fields = [
            "id",
            "user",
            "created_at",
            "updated_at",
            "is_featured",
            "images"
        ]

class FavoriteSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = Favorite
        fields = ["id", "product", "created_at"]
        read_only_fields = ["id", "product", "created_at"]
        

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            "id",
            "product",
            "quantity",
            "total_price",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "product",
            "total_price",
            "created_at",
            "updated_at",
        ]

    def get_total_price(self, obj):
        return obj.product.price * obj.quantity


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = [
            "id",
            "items",
            "total_price",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "items",
            "total_price",
            "created_at",
            "updated_at",
        ]

    def get_total_price(self, obj):
        total = 0

        for item in obj.items.all():
            total += item.product.price * item.quantity

        return total