
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth.models import User

from api.models import Product

from django.core.cache import cache
from unittest.mock import patch


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

    def test_product_list_uses_cache(self):
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

    def test_product_list_returns_200(self):
        response = self.client.get("/api/products/")

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

    def test_product_list_contains_created_product(self):
        response = self.client.get("/api/products/")

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        products = response.data["results"]

        product_titles = [
            product["title"] for product in products
        ]

        self.assertIn("Test Telefonu", product_titles)

    def test_product_list_excludes_inactive_products(self):
        Product.objects.create(
            user=self.user,
            title="Pasif Test Telefonu",
            description="Listede görünmemeli",
            price="10000.00",
            stock=5,
            is_active=False
        )

        response = self.client.get("/api/products/")

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        product_titles = [
            product["title"]
            for product in response.data["results"]
        ]

        self.assertIn("Test Telefonu", product_titles)
        self.assertNotIn("Pasif Test Telefonu", product_titles)

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
            "jwt_test_user",
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
