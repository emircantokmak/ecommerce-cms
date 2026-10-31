from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.core.cache import cache
from django.core import mail
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

    def test_product_list_response_is_cached(self):
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


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", DEFAULT_FROM_EMAIL="noreply@example.com")
class ProductEmailNotificationTests(TestCase, TestDataMixin):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="seller_mail", email="seller@example.com", password="StrongPass123!"
        )
        self.client.force_authenticate(user=self.user)
        mail.outbox = []

    def test_product_create_sends_email_to_actor(self):
        response = self.client.post("/api/user/products/", {
            "title": "Yeni ürün", "description": "Açıklama", "price": "125.50",
            "stock": 4, "is_active": True,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user.email])
        self.assertIn("oluşturuldu", mail.outbox[0].body)

    def test_product_update_sends_email_to_actor(self):
        product = self.make_product(user=self.user)
        response = self.client.patch(f"/api/user/products/{product.id}/", {"title": "Güncel ürün"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("güncellendi", mail.outbox[0].body)

    def test_product_delete_sends_email_to_actor(self):
        product = self.make_product(user=self.user)
        response = self.client.delete(f"/api/user/products/{product.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("silindi", mail.outbox[0].body)

    def test_product_mail_failure_does_not_fail_product_creation(self):
        with patch("api.email_service.EmailMultiAlternatives.send", side_effect=RuntimeError("SMTP kapalı")):
            response = self.client.post("/api/user/products/", {
                "title": "Mail hatalı ürün", "description": "Açıklama", "price": "10.00",
                "stock": 1, "is_active": True,
            }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Product.objects.filter(title="Mail hatalı ürün").exists())


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", DEFAULT_FROM_EMAIL="noreply@example.com")
class AccountEmailNotificationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="account_user", email="old@example.com", password="StrongPass123!"
        )
        self.client.force_authenticate(user=self.user)
        mail.outbox = []

    def test_email_change_notifies_old_and_new_addresses(self):
        response = self.client.post("/api/user/change-email/", {
            "current_password": "StrongPass123!", "new_email": "new@example.com",
            "new_email_confirm": "new@example.com",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "new@example.com")
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual({m.to[0] for m in mail.outbox}, {"old@example.com", "new@example.com"})

    def test_email_change_rejects_mismatched_confirmation(self):
        response = self.client.post("/api/user/change-email/", {
            "current_password": "StrongPass123!", "new_email": "new@example.com",
            "new_email_confirm": "different@example.com",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "old@example.com")
        self.assertEqual(len(mail.outbox), 0)

    def test_username_change_sends_notification(self):
        response = self.client.post("/api/user/change-username/", {
            "current_password": "StrongPass123!", "new_username": "new_account_name",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("new_account_name", mail.outbox[0].body)

    def test_password_change_sends_notification_without_password(self):
        response = self.client.post("/api/user/change-password/", {
            "current_password": "StrongPass123!", "new_password": "AnotherStrongPass456!",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("AnotherStrongPass456!"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertNotIn("AnotherStrongPass456!", mail.outbox[0].body)

    def test_account_delete_requires_password(self):
        response = self.client.delete("/api/user/account/", {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(User.objects.filter(pk=self.user.pk).exists())

    def test_account_delete_sends_notification_and_deletes_user(self):
        user_id = self.user.pk
        response = self.client.delete("/api/user/account/", {"current_password": "StrongPass123!"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(pk=user_id).exists())
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("silindi", mail.outbox[0].subject)

    def test_registration_sends_verification_email(self):
        self.client.force_authenticate(user=None)
        response = self.client.post("/api/user/register/", {
            "username": "new_registered", "email": "register@example.com", "password": "RegisterPass123!",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("verify-email", mail.outbox[0].body)
        registered = User.objects.get(username="new_registered")
        self.assertFalse(registered.is_active)

    def test_verification_token_activates_account(self):
        self.client.force_authenticate(user=None)
        self.client.post("/api/user/register/", {
            "username": "verify_user", "email": "verify@example.com", "password": "RegisterPass123!",
        }, format="json")
        body = mail.outbox[-1].body
        token = body.split("token=", 1)[1].split()[0]
        response = self.client.get(f"/api/user/verify-email/?token={token}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(User.objects.get(username="verify_user").is_active)


class CategoryAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(name="Elektronik", slug="elektronik")
        self.normal_user = User.objects.create_user(username="category_user", password="StrongPass123!")
        self.admin = User.objects.create_superuser(username="category_admin", email="admin@example.com", password="StrongPass123!")

    def test_category_list_is_public(self):
        response = self.client.get("/api/categories/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"][0]["slug"], "elektronik")

    def test_category_detail_is_public(self):
        response = self.client.get(f"/api/categories/{self.category.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Elektronik")

    def test_category_create_requires_admin(self):
        response = self.client.post("/api/categories/", {"name": "Kitap", "slug": "kitap"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_can_create_category(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post("/api/categories/", {"name": "Kitap", "slug": "kitap"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Category.objects.filter(slug="kitap").exists())

    def test_admin_can_update_category(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(f"/api/categories/{self.category.id}/", {"name": "Elektronik Ürünler"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.category.refresh_from_db()
        self.assertEqual(self.category.name, "Elektronik Ürünler")

    def test_non_admin_cannot_delete_category(self):
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.delete(f"/api/categories/{self.category.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Category.objects.filter(pk=self.category.pk).exists())

    def test_admin_can_delete_category(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(f"/api/categories/{self.category.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Category.objects.filter(pk=self.category.pk).exists())

    def test_missing_category_returns_404(self):
        response = self.client.get("/api/categories/99999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class PublicProductAPITests(TestCase, TestDataMixin):
    def setUp(self):
        self.client = APIClient()
        self.user = self.make_user(username="public_product_owner")
        self.category = Category.objects.create(name="Telefon", slug="telefon")
        self.first = self.make_product(user=self.user, title="Telefon Alpha", description="Akıllı telefon", price=Decimal("100.00"), category=self.category)
        self.second = self.make_product(user=self.user, title="Telefon Beta", description="Başka model", price=Decimal("250.00"), category=self.category)
        self.inactive = self.make_product(user=self.user, title="Gizli Telefon", is_active=False)
        cache.clear()

    def test_public_list_excludes_inactive_products(self):
        response = self.client.get("/api/products/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in response.data["results"]]
        self.assertIn(self.first.id, ids)
        self.assertIn(self.second.id, ids)
        self.assertNotIn(self.inactive.id, ids)

    def test_product_filter_by_category_slug(self):
        response = self.client.get("/api/products/?category=telefon")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)

    def test_product_filter_by_minimum_and_maximum_price(self):
        response = self.client.get("/api/products/?min_price=150&max_price=300")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.second.id)

    def test_product_search_matches_title_or_description(self):
        response = self.client.get("/api/products/?search=Akıllı")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.first.id)

    def test_product_ordering_by_price(self):
        response = self.client.get("/api/products/?ordering=price")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"][0]["id"], self.first.id)

    def test_product_detail_returns_active_product(self):
        response = self.client.get(f"/api/products/{self.first.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Telefon Alpha")

    def test_product_detail_hides_inactive_product(self):
        response = self.client.get(f"/api/products/{self.inactive.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_product_list_contains_only_owner_products(self):
        other = self.make_user(username="another_product_owner")
        self.make_product(user=other, title="Başkasının ürünü")
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/user/products/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        self.assertTrue(all(item["user"] == self.user.username for item in response.data))

    def test_owner_can_update_product(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(f"/api/user/products/{self.first.id}/", {"title": "Yeni başlık"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.first.refresh_from_db()
        self.assertEqual(self.first.title, "Yeni başlık")

    def test_owner_cannot_create_product_with_invalid_price(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post("/api/user/products/", {
            "title": "Hatalı ürün", "description": "Açıklama", "price": "-1.00", "stock": 2,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class FeaturedProductAPITests(TestCase, TestDataMixin):
    def setUp(self):
        self.client = APIClient()
        self.user = self.make_user(username="featured_owner")
        self.admin = User.objects.create_superuser(username="featured_admin", email="featured@example.com", password="StrongPass123!")
        self.featured = self.make_product(user=self.user, title="Öne çıkan", is_featured=True)
        self.ordinary = self.make_product(user=self.user, title="Normal ürün")

    def test_featured_list_is_public_and_only_contains_featured_active_products(self):
        response = self.client.get("/api/products/featured/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in response.data], [self.featured.id])

    def test_only_admin_can_create_featured_product(self):
        response = self.client.post("/api/products/featured/", {
            "title": "Admin ürünü", "description": "Açıklama", "price": "20.00", "stock": 2,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_can_create_featured_product(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post("/api/products/featured/", {
            "title": "Admin ürünü", "description": "Açıklama", "price": "20.00", "stock": 2,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Product.objects.get(title="Admin ürünü").is_featured)

    def test_admin_can_remove_product_from_featured_list(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(f"/api/products/featured/{self.featured.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.featured.refresh_from_db()
        self.assertFalse(self.featured.is_featured)

    def test_non_admin_cannot_manage_featured_product(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(f"/api/products/featured/{self.featured.id}/", {"title": "Değiştir"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
