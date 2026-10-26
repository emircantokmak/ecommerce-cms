from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from api.models import Cart, CartItem, Category, Favorite, Product, ProductImage

from api.serializers import (
    CartItemSerializer,
    CartSerializer,
    ProductImageSerializer,
    ProductSerializer,
    RegisterSerializer,
    UserProfileUpdateSerializer,
)
class ProductListAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            username="testuser",
            password="TestPassword123"
        )

        self.product = Product.objects.create(
            user=self.user,
            title="Test Telefonu",
            description="Test açıklaması",
            price="15000.00",
            stock=10,
            is_active=True
        )


        cache.clear()

        with patch(
            "api.views.Product.objects.filter",
            wraps=Product.objects.filter
        ) as mock_filter:
            first_response = self.client.get("/api/products/")
            second_response = self.client.get("/api/products/")

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)
        self.assertEqual(mock_filter.call_count, 1)

class ProductAuthorizationAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_unauthenticated_user_cannot_create_product(self):
        response = self.client.post(
            "/api/user/products/",
            {
                "title": "Yetkisiz Ürün",
                "description": "Bu ürün oluşturulmamalı",
                "price": "1000.00",
                "stock": 5,
                "is_active": True,
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

    def test_user_cannot_delete_another_users_product(self):
        owner = User.objects.create_user(
            username="product_owner",
            password="OwnerPassword123"
        )

        another_user = User.objects.create_user(
            username="another_user",
            password="AnotherPassword123"
        )

        product = Product.objects.create(
            user=owner,
            title="Başkasının Ürünü",
            description="Silinmemeli",
            price="2000.00",
            stock=5,
            is_active=True
        )

        self.client.force_authenticate(user=another_user)

        response = self.client.delete(
            f"/api/user/products/{product.id}/"
        )

        self.assertIn(response.status_code, [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        ])

        self.assertTrue(
            Product.objects.filter(id=product.id).exists()
        )

    def test_user_can_delete_own_product(self):
        user = User.objects.create_user(
            username="my_product_user",
            password="MyPassword123"
        )

        product = Product.objects.create(
            user=user,
            title="Kendi Ürünüm",
            description="Silinebilir",
            price="1500.00",
            stock=3,
            is_active=True
        )

        self.client.force_authenticate(user=user)

        response = self.client.delete(
            f"/api/user/products/{product.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT
        )

        self.assertFalse(
            Product.objects.filter(id=product.id).exists()
        )

class JWTAuthenticationAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            username="jwt_test_user",
            email="jwt@example.com",
            password="SecurePassword123"
        )

    def test_login_returns_access_and_refresh_tokens(self):
        response = self.client.post(
            "/api/user/login/",
            {
                "username": "jwt_test_user",
                "password": "SecurePassword123",
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertIn("user", response.data)

    
    def test_access_token_can_retrieve_profile(self):
        login_response = self.client.post(
            "/api/user/login/",
            {
                "username": "jwt_test_user",
                "password": "SecurePassword123",
            },
            format="json"
        )

        access_token = login_response.data["access"]

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )

        profile_response = self.client.get(
            "/api/user/profile/"
        )

        self.assertEqual(
            profile_response.status_code,
            status.HTTP_200_OK
        )
        
        self.assertEqual(
            profile_response.data["data"]["username"],
            "jwt_test_user"
        )

    
    def test_login_rejects_incorrect_password(self):
        response = self.client.post(
            "/api/user/login/",
            {
                "username": "jwt_test_user",
                "password": "WrongPassword123",
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)
        



class TestDataMixin:
    def make_user(
        self,
        username="testuser",
        password="Testpass123!",
        is_staff=False
    ):
        return User.objects.create_user(
            username=username,
            password=password,
            is_staff=is_staff
        )

    def make_product(self, user=None, **kwargs):
        if user is None:
            user = self.make_user()

        values = {
            "user": user,
            "title": "Test ürün",
            "description": "Test açıklaması",
            "price": Decimal("100.00"),
            "stock": 10,
            "is_active": True,
        }

        values.update(kwargs)

        return Product.objects.create(**values)
    

class FavoriteAPITests(TestCase, TestDataMixin):
    def setUp(self):
        self.client = APIClient()
        self.user = self.make_user(username="favorite_user")
        self.product = self.make_product(user=self.user)

    def test_favorites_requires_login(self):
        response = self.client.get("/api/favorites/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_can_add_product_to_favorites(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f"/api/favorites/{self.product.id}/")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Favorite.objects.filter(user=self.user, product=self.product).exists())

    def test_user_cannot_add_same_favorite_twice(self):
        Favorite.objects.create(user=self.user, product=self.product)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f"/api/favorites/{self.product.id}/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_favorite_list_only_contains_current_users_favorites(self):
        other = self.make_user(username="another_favorite_user")
        other_product = self.make_product(user=other, title="Diğer ürün")
        Favorite.objects.create(user=other, product=other_product)
        Favorite.objects.create(user=self.user, product=self.product)
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/favorites/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["product"]["id"], self.product.id)

    def test_user_can_remove_favorite(self):
        Favorite.objects.create(user=self.user, product=self.product)
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f"/api/favorites/{self.product.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Favorite.objects.filter(user=self.user, product=self.product).exists())


    def test_favorite_cannot_be_added_for_inactive_product(self):
        self.product.is_active = False
        self.product.save()
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f"/api/favorites/{self.product.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class CartAPITests(TestCase, TestDataMixin):
    def setUp(self):
        self.client = APIClient()
        self.user = self.make_user(username="cart_user")
        self.product = self.make_product(user=self.user, price=Decimal("15.00"), stock=5)

    def test_cart_requires_login(self):
        response = self.client.get("/api/cart/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_cart_creates_empty_cart(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/cart/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["items"], [])
        self.assertEqual(Cart.objects.filter(user=self.user).count(), 1)

    def test_add_product_to_cart(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post("/api/cart/", {"product_id": self.product.id, "quantity": 2}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CartItem.objects.get(cart__user=self.user, product=self.product).quantity, 2)

    def test_add_product_rejects_zero_quantity(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post("/api/cart/", {"product_id": self.product.id, "quantity": 0}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_product_rejects_quantity_over_stock(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post("/api/cart/", {"product_id": self.product.id, "quantity": 6}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_inactive_product_to_cart_fails(self):
        self.product.is_active = False
        self.product.save()
        self.client.force_authenticate(user=self.user)
        response = self.client.post("/api/cart/", {"product_id": self.product.id, "quantity": 1}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_adding_same_product_increases_quantity(self):
        self.client.force_authenticate(user=self.user)
        self.client.post("/api/cart/", {"product_id": self.product.id, "quantity": 1}, format="json")
        response = self.client.post("/api/cart/", {"product_id": self.product.id, "quantity": 2}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CartItem.objects.get(cart__user=self.user, product=self.product).quantity, 3)

    def test_cart_item_quantity_can_be_updated(self):
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(cart=cart, product=self.product, quantity=1)
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(f"/api/cart/items/{item.id}/", {"quantity": 4}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item.refresh_from_db()
        self.assertEqual(item.quantity, 4)

    def test_cart_item_cannot_be_updated_by_another_user(self):
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(cart=cart, product=self.product, quantity=1)
        other = self.make_user(username="other_cart_user")
        self.client.force_authenticate(user=other)
        response = self.client.patch(f"/api/cart/items/{item.id}/", {"quantity": 2}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cart_item_can_be_deleted(self):
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(cart=cart, product=self.product, quantity=1)
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f"/api/cart/items/{item.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(CartItem.objects.filter(id=item.id).exists())


    def test_cart_rejects_missing_product_id(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post("/api/cart/", {"quantity": 1}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cart_rejects_non_numeric_quantity(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            "/api/cart/",
            {"product_id": self.product.id, "quantity": "abc"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cart_item_update_rejects_quantity_over_stock(self):
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(cart=cart, product=self.product, quantity=1)
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            f"/api/cart/items/{item.id}/",
            {"quantity": 99},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ProductImageAPITests(TestCase, TestDataMixin):
    def setUp(self):
        self.client = APIClient()
        self.user = self.make_user(username="image_owner")
        self.other_user = self.make_user(username="image_other")
        self.product = self.make_product(user=self.user)
        self.image = ProductImage.objects.create(
            product=self.product,
            image="https://example.com/image.jpg",
            is_main=True,
        )

    def test_product_images_requires_login(self):
        response = self.client.get(f"/api/user/products/{self.product.id}/images/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_owner_can_list_product_images(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f"/api/user/products/{self.product.id}/images/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_other_user_cannot_list_product_images(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(f"/api/user/products/{self.product.id}/images/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_owner_can_update_image(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            f"/api/user/products/{self.product.id}/images/{self.image.id}/",
            {"is_main": False}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.image.refresh_from_db()
        self.assertFalse(self.image.is_main)

    @patch("api.views.delete_product_image")
    def test_owner_can_delete_image(self, delete_image):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f"/api/user/products/{self.product.id}/images/{self.image.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        delete_image.assert_called_once_with(self.image.image)
        self.assertFalse(ProductImage.objects.filter(id=self.image.id).exists())

    @patch("api.views.upload_product_image", return_value="https://example.com/uploaded.jpg")
    def test_owner_can_upload_image(self, upload_image):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            f"/api/user/products/{self.product.id}/images/",
            {"image": SimpleUploadedFile("test.jpg", b"fake-image", content_type="image/jpeg"), "is_main": "true"},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(ProductImage.objects.filter(product=self.product, image="https://example.com/uploaded.jpg").exists())

    def test_image_upload_requires_file(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            f"/api/user/products/{self.product.id}/images/",
            {"is_main": "true"},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    @patch("api.views.upload_product_image", side_effect=ValueError("Geçersiz görsel"))
    def test_image_upload_returns_bad_request_for_invalid_file(self, upload_image):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            f"/api/user/products/{self.product.id}/images/",
            {"image": SimpleUploadedFile("test.txt", b"not-image", content_type="text/plain")},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        upload_image.assert_called_once()
