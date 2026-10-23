from django.contrib.auth import authenticate
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework import status
from api.supabase_storage import delete_product_image
from api.supabase_storage import upload_product_image
from .permissions import IsProductOwner
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.exceptions import ValidationError

from django.core.cache import cache
from hashlib import md5

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError  
from django.core.validators import validate_email 
from .serializers import (
    CartItemSerializer,
    CartSerializer,
    FavoriteSerializer,
    UserSerializer,
    RegisterSerializer,
    CategorySerializer,
    ProductSerializer,
    ProductImageSerializer,
    UserProfileUpdateSerializer
)

from .models import Cart, CartItem, Category, Favorite, Product, ProductImage

from .filters import ProductFilter

User = get_user_model()

class RegisterView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        serializer = RegisterSerializer(
            data=request.data
        )

        if serializer.is_valid():

            user = serializer.save()

            return Response(
                {
                    "message": "User created successfully.",
                    "user": UserSerializer(user).data
                },
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class LoginView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:

            return Response(
                {
                    "detail": "Username and password are required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(
            username=username,
            password=password
        )

        if user is None:

            return Response(
                {
                    "detail": "Invalid credentials."
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserSerializer(user).data
            },
            status=status.HTTP_200_OK
        )


class ProfileView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        serializer = UserSerializer(
            request.user
        )

        return Response({
            "message":"User Profile Data",
            "data": serializer.data
        }
        )


# CATEGORY


class ProfileView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response({
            "message":"Profile Information",
            "data":serializer.data
            })

    def patch(self, request):
        serializer = UserProfileUpdateSerializer(
            request.user,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()

            return Response({
                "message":"User Profile Data Updated",
                "data":UserSerializer(request.user).data
            },status=status.HTTP_200_OK
            )

        return Response({
            "message":"Profile Update Failed.",
            "error":serializer.errors
        },status=status.HTTP_400_BAD_REQUEST
        )

class ChangeEMailView(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request):
        current_password = request.data.get("current_password")
        new_email = request.data.get("new_email")
        new_email_confirm = request.data.get("new_email_confirm")
        
        if not new_email or not new_email_confirm:
            return Response(
                {
                    "detail": (
                        "Yeni E-Mail ve yeni  doğrulama E-Mail zorunludur."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        elif not current_password:
            return Response(
                {
                    "detail": (
                        "Mevcut şifre zorunludur."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )
            
        user = request.user
        
        if not user.check_password(current_password):
            return Response(
                {"current_password": ["Mevcut şifre yanlış."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            validate_email(new_email)
        except ValidationError:
            return Response(
                {"new_email": ["Geçerli bir e-posta adresi giriniz."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            User.objects.filter(email=new_email)
            .exclude(pk=user.pk)
            .exists()
        ):
            return Response(
                {"new_email": ["Bu e-posta adresi zaten kullanımda."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.email = new_email
        user.save(update_fields=["email"])

        return Response(
            {"message": "E-posta adresi başarıyla değiştirildi."},
            status=status.HTTP_200_OK,
        )
        
        
    
    
class ChangeUserNameView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        current_password = request.data.get("current_password")
        new_username = request.data.get("new_username")

        if not current_password or not new_username:
            return Response(
                {
                    "detail": (
                        "Mevcut şifre ve yeni kullanıcı adı zorunludur."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user

        if not user.check_password(current_password):
            return Response(
                {"current_password": ["Mevcut şifre yanlış."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        username_field = user._meta.get_field("username")
        try:
            username_field.clean(new_username, user)
        except ValidationError as exc:
            return Response(
                {"new_username": list(exc.messages)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            User.objects.filter(username=new_username)
            .exclude(pk=user.pk)
            .exists()
        ):
            return Response(
                {"new_username": ["Bu kullanıcı adı zaten alınmış."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.username = new_username
        user.save(update_fields=["username"])

        return Response(
            {"message": "Kullanıcı adı başarıyla değiştirildi."},
            status=status.HTTP_200_OK,
        )

class ChangePasswordView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):
        current_password = request.data.get("current_password")
        new_password = request.data.get("new_password")

        if not current_password or not new_password:
            return Response(
                {
                    "detail": (
                        "Mevcut şifre ve yeni şifre zorunludur."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        user = request.user
        if not user.check_password(current_password):
            return Response(
                {"current_password": ["Mevcut şifre yanlış."]},
                status=status.HTTP_400_BAD_REQUEST
            )


        if not user.check_password(current_password):
            return Response(
                {"current_password": ["Mevcut şifre yanlış."]},
                status=status.HTTP_400_BAD_REQUEST
            )

        from django.contrib.auth.password_validation import (
            validate_password
        )
        from django.core.exceptions import ValidationError

        try:
            validate_password(new_password, user=user)
        except ValidationError as exc:
            return Response(
                {"new_password": list(exc.messages)},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new_password)
        user.save(update_fields=["password"])

        return Response(
            {"message": "Şifre başarıyla değiştirildi."},
            status=status.HTTP_200_OK
        )


class CategoryListView(APIView):

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdminUser()]

        return [AllowAny()]

    def get(self, request):
        categories = Category.objects.all()

        serializer = CategorySerializer(
            categories,
            many=True
        )

        return Response({
            "data":serializer.data
        })

    def post(self, request):
        serializer = CategorySerializer(
            data=request.data
        )

        if serializer.is_valid():
            serializer.save()

            return Response({
                "message":"Category Created Succesfull",
                "data":serializer.data
                },
                status=status.HTTP_201_CREATED
            )

        return Response({
            "message":"Category Create Failed",
            "error":serializer.errors,
        },status=status.HTTP_400_BAD_REQUEST
        )

class CategoryDetailView(APIView):

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [IsAdminUser()]

        return [AllowAny()]

    def get_category(self, category_id):
        try:
            return Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            return None

    def get(self, request, category_id):
        category = self.get_category(category_id)

        if category is None:
            return Response(
                {"detail": "Category not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = CategorySerializer(category)

        return Response(serializer.data)

    def put(self, request, category_id):
        category = self.get_category(category_id)

        if category is None:
            return Response(
                {"detail": "Category not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = CategorySerializer(
            category,
            data=request.data
        )

        if serializer.is_valid():
            serializer.save()

            return Response({
                "message":"Category Detail Updated Succesfull.",
                "data":serializer.data
            },status=status.HTTP_200_OK)

        return Response({
            "message":"Category Detail Update Failed",
            "error":serializer.errors,
        },status=status.HTTP_400_BAD_REQUEST
        )

    def patch(self, request, category_id):
        category = self.get_category(category_id)

        if category is None:
            return Response(
                {"detail": "Category not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = CategorySerializer(
            category,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()

            return Response({
                "message":"Category Detail Updated Successfull",
                "data":serializer.data
            },status=status.HTTP_200_OK)

        return Response({
            "message":"Category Detail Update Failed",
            "error":serializer.errors,
        },status=status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request, category_id):
        category = self.get_category(category_id)

        if category is None:
            return Response(
                {"detail": "Category not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        category.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )

# PRODUCTS

class ProductListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        cache_key = "products:" + md5(
            request.get_full_path().encode()
        ).hexdigest()

        cached_data = cache.get(cache_key)

        if cached_data is not None:
            return Response(cached_data)

        products = Product.objects.filter(
            is_active=True
        ).order_by("-created_at")

        product_filter = ProductFilter(
            request.GET,
            queryset=products
        )

        products = product_filter.qs

        ordering = request.GET.get("ordering")

        allowed_ordering = [
            "price",
            "-price",
            "created_at",
            "-created_at",
            "title",
            "-title"
        ]

        if ordering in allowed_ordering:
            products = products.order_by(ordering)

        paginator = PageNumberPagination()
        paginator.page_size = 5

        page = paginator.paginate_queryset(
            products,
            request
        )

        serializer = ProductSerializer(
            page,
            many=True
        )

        response = paginator.get_paginated_response(
            serializer.data
        )

        cache.set(
            cache_key,
            response.data,
            timeout=60
        )

        return response


class ProductDetailView(APIView):

    permission_classes = [AllowAny]

    def get(self, request, product_id):

        try:

            product = Product.objects.get(
                id=product_id,
                is_active=True
            )

        except Product.DoesNotExist:

            return Response(
                {
                    "detail": "Product not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ProductSerializer(
            product
        )

        return Response(
            serializer.data
        )


# USER PRODUCTS

class UserProductView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        products = Product.objects.filter(
            user=request.user
        ).order_by("-created_at")

        serializer = ProductSerializer(
            products,
            many=True
        )

        return Response(
            serializer.data
        )

    def post(self, request):

        serializer = ProductSerializer(
            data=request.data
        )

        if serializer.is_valid():

            product = serializer.save(
                user=request.user
            )
            
            cache.clear()


            return Response({
                "message":"Product Created Successfull.",
                "data":ProductSerializer(product).data,
            },status=status.HTTP_201_CREATED
            )

        return Response({
            "message":"Product Create Failed",
            "error":serializer.errors,
        },status=status.HTTP_400_BAD_REQUEST
        )


class UserProductDetailView(APIView):
    permission_classes = [IsAuthenticated, IsProductOwner]

    def get_product(self, product_id, user):
        try:
            return Product.objects.get(
                id=product_id,
                user=user
            )
        except Product.DoesNotExist:
            return None

    def put(self, request, product_id):
        product = self.get_product(
            product_id,
            request.user
        )

        if product is None:
            return Response(
                {"detail": "Product not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        self.check_object_permissions(request, product)

        serializer = ProductSerializer(
            product,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            cache.clear()
            return Response({
                "message":"Product Detail Updated Successfull",
                "data":serializer.data
                },status=status.HTTP_200_OK)

        return Response({
            "message":"Product Detail Update Failed",
            "error":serializer.errors
        },status=status.HTTP_400_BAD_REQUEST
        )

    def patch(self, request, product_id):
        return self.put(request, product_id)

    def delete(self, request, product_id):
        product = self.get_product(
            product_id,
            request.user
        )

        if product is None:
            return Response(
                {"detail": "Product not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        self.check_object_permissions(request, product)

        product.delete()
        cache.clear()
        return Response({
            "message":"Product Not Found."
        },status=status.HTTP_204_NO_CONTENT
        )
# PRODUCT IMAGES

class ProductImageListView(APIView):
    permission_classes = [IsAuthenticated]

    def get_product(self, product_id, user):
        try:
            return Product.objects.get(
                id=product_id,
                user=user,
            )
        except Product.DoesNotExist:
            return None

    def get(self, request, product_id):
        product = self.get_product(product_id, request.user)

        if product is None:
            return Response(
                {"detail": "Product not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        images = ProductImage.objects.filter(
            product=product
        ).order_by("-is_main", "created_at")

        serializer = ProductImageSerializer(images, many=True)
        return Response(serializer.data)

    def post(self, request, product_id):
        product = self.get_product(product_id, request.user)

        if product is None:
            return Response(
                {"detail": "Product not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        image_file = request.FILES.get("image")

        if image_file is None:
            return Response(
                {"image": ["Bu alan zorunludur."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        is_main = request.data.get("is_main", "false")

        if str(is_main).lower() not in ["true", "false", "1", "0"]:
            return Response(
                {"is_main": ["true veya false olmalıdır."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        is_main = str(is_main).lower() in ["true", "1"]

        try:
            image_url = upload_product_image(image_file)
        except ValueError as exc:
            return Response(
                {"image": [str(exc)]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception:
            return Response(
                {"detail": "Görsel yüklenemedi. Supabase ayarlarını kontrol edin."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        if is_main:
            ProductImage.objects.filter(
                product=product
            ).update(is_main=False)

        image = ProductImage.objects.create(
            product=product,
            image=image_url,
            is_main=is_main,
        )

        serializer = ProductImageSerializer(image)
        return Response({
            "message":"Product Image Created Successfull.",
            "data":serializer.data
        },status=status.HTTP_201_CREATED,
        )


class ProductImageDetailView(APIView):

    permission_classes = [IsAuthenticated]

    def get_image(self, product_id, image_id, user):
        try:
            return ProductImage.objects.get(
                id=image_id,
                product__id=product_id,
                product__user=user
            )
        except ProductImage.DoesNotExist:
            return None

    def patch(self, request, product_id, image_id):
        image = self.get_image(
            product_id,
            image_id,
            request.user
        )

        if image is None:
            return Response(
                {"detail": "Image not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ProductImageSerializer(
            image,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            image = serializer.save()

            return Response({
                "message":"Product Image Updated Successfull.",
                "data":ProductImageSerializer(image).data
            },status=status.HTTP_200_OK
            )

        return Response({
            "message":"Product Image Update Failed",
            "error":serializer.errors
        },status=status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request, product_id, image_id):
        image = self.get_image(
            product_id,
            image_id,
            request.user
        )

        if image is None:
            return Response(
                {"detail": "Image not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            delete_product_image(image.image)
        except Exception:
            return Response(
                {
                    "detail": (
                        "Supabase görseli silinemedi. "
                        "Lütfen tekrar deneyin."
                    )
                },
                status=status.HTTP_502_BAD_GATEWAY
            )

        image.delete()

        return Response({
            "message":"Content Not"
        },status=status.HTTP_204_NO_CONTENT
        )
        


class FeaturedProductListView(APIView):
    """
    Öne çıkarılmış ürünleri listeler.
    Admin kullanıcı yeni öne çıkarılmış ürün oluşturabilir.
    """

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdminUser()]
        return [AllowAny()]

    def get(self, request):
        products = Product.objects.filter(
            is_active=True,
            is_featured=True
        ).select_related(
            "category",
            "user"
        ).prefetch_related(
            "images"
        ).order_by(
            "-created_at",
            "-id"
        )

        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ProductSerializer(data=request.data)

        if serializer.is_valid():
            product = serializer.save(
                user=request.user,
                is_featured=True
            )

            return Response(
                ProductSerializer(product).data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class FeaturedProductDetailView(APIView):
    """
    Admin:
    - PUT/PATCH: Öne çıkarılmış ürünü günceller.
    - DELETE: Ürünü öne çıkarılmış listesinden kaldırır.
    """

    permission_classes = [IsAdminUser]

    def get_product(self, product_id):
        return Product.objects.filter(
            id=product_id,
            is_featured=True
        ).first()

    def put(self, request, product_id):
        product = self.get_product(product_id)

        if product is None:
            return Response(
                {"detail": "Öne çıkarılmış ürün bulunamadı."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ProductSerializer(
            product,
            data=request.data
        )

        if serializer.is_valid():
            updated_product = serializer.save(
                is_featured=True
            )

            return Response(
                ProductSerializer(updated_product).data,
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def patch(self, request, product_id):
        product = self.get_product(product_id)

        if product is None:
            return Response(
                {"detail": "Öne çıkarılmış ürün bulunamadı."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ProductSerializer(
            product,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            updated_product = serializer.save(
                is_featured=True
            )

            return Response(
                ProductSerializer(updated_product).data,
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request, product_id):
        product = self.get_product(product_id)

        if product is None:
            return Response(
                {"detail": "Öne çıkarılmış ürün bulunamadı."},
                status=status.HTTP_404_NOT_FOUND
            )

        product.is_featured = False
        product.save(update_fields=["is_featured"])

        return Response(
            {"detail": "Ürün öne çıkarılmış listesinden kaldırıldı."},
            status=status.HTTP_200_OK
        )

class FavoriteListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        favorites = Favorite.objects.filter(
            user=request.user
        ).select_related(
            "product",
            "product__category"
        ).prefetch_related(
            "product__images"
        )

        serializer = FavoriteSerializer(
            favorites,
            many=True
        )

        return Response(serializer.data)

    def post(self, request, product_id):
        try:
            product = Product.objects.get(
                id=product_id,
                is_active=True
            )
        except Product.DoesNotExist:
            return Response(
                {"detail": "Product not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        favorite, created = Favorite.objects.get_or_create(
            user=request.user,
            product=product
        )

        if not created:
            return Response(
                {"detail": "Product is already in favorites."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = FavoriteSerializer(favorite)

        return Response({
            "message":"Product created in favorites successfull",
            "data":serializer.data
        },status=status.HTTP_201_CREATED
        )

    def delete(self, request, product_id):
        try:
            favorite = Favorite.objects.get(
                user=request.user,
                product_id=product_id
            )
        except Favorite.DoesNotExist:
            return Response(
                {"detail": "Favorite not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        favorite.delete()

        return Response({
            "message":"Favorite not found."  
        },
            status=status.HTTP_204_NO_CONTENT
        )
        
class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart, created = Cart.objects.get_or_create(
            user=request.user
        )

        serializer = CartSerializer(cart)

        return Response(serializer.data)

    def post(self, request):
        product_id = request.data.get("product_id")
        quantity = request.data.get("quantity", 1)

        if not product_id:
            return Response(
                {"detail": "product_id is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            return Response(
                {"detail": "Quantity must be a valid number."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if quantity <= 0:
            return Response(
                {"detail": "Quantity must be greater than 0."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            product = Product.objects.get(
                id=product_id,
                is_active=True
            )
        except Product.DoesNotExist:
            return Response(
                {"detail": "Product not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        if product.stock < quantity:
            return Response(
                {"detail": "Not enough stock."},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart, created = Cart.objects.get_or_create(
            user=request.user
        )

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={
                "quantity": quantity
            }
        )

        if not created:
            new_quantity = cart_item.quantity + quantity

            if new_quantity > product.stock:
                return Response(
                    {"detail": "Not enough stock."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            cart_item.quantity = new_quantity
            cart_item.save()

        serializer = CartItemSerializer(cart_item)

        return Response({
            "message":"Cart Created Successfull.",
            "data":serializer.data},
            status=status.HTTP_201_CREATED
        )

class CartItemDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_cart_item(self, request, item_id):
        try:
            return CartItem.objects.get(
                id=item_id,
                cart__user=request.user
            )
        except CartItem.DoesNotExist:
            return None

    def patch(self, request, item_id):
        cart_item = self.get_cart_item(
            request,
            item_id
        )

        if cart_item is None:
            return Response(
                {"detail": "Cart item not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        quantity = request.data.get("quantity")

        if quantity is None:
            return Response(
                {"detail": "Quantity is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            return Response(
                {"detail": "Quantity must be a valid number."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if quantity <= 0:
            return Response(
                {"detail": "Quantity must be greater than 0."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if quantity > cart_item.product.stock:
            return Response(
                {"detail": "Not enough stock."},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart_item.quantity = quantity
        cart_item.save()

        serializer = CartItemSerializer(cart_item)

        return Response({
            "data":serializer.data
        })

    def delete(self, request, item_id):
        cart_item = self.get_cart_item(
            request,
            item_id
        )

        if cart_item is None:
            return Response(
                {"detail": "Cart item not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        cart_item.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )
        
        
class CartItemCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        product_id = request.data.get("product_id")
        quantity = request.data.get("quantity", 1)

        if not product_id:
            return Response(
                {"detail": "product_id is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            return Response(
                {"detail": "Quantity must be a valid number."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if quantity <= 0:
            return Response(
                {"detail": "Quantity must be greater than 0."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            product = Product.objects.get(
                id=product_id,
                is_active=True
            )
        except Product.DoesNotExist:
            return Response(
                {"detail": "Product not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        if product.stock < quantity:
            return Response(
                {"detail": "Not enough stock."},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart, created = Cart.objects.get_or_create(
            user=request.user
        )

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={
                "quantity": quantity
            }
        )

        if not created:
            new_quantity = cart_item.quantity + quantity

            if new_quantity > product.stock:
                return Response(
                    {"detail": "Not enough stock."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            cart_item.quantity = new_quantity
            cart_item.save()

        serializer = CartItemSerializer(cart_item)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )