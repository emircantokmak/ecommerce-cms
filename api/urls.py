from django.urls import path

from .views import (
    RegisterView,
    LoginView,
    ProfileView,
    ChangePasswordView,
    CategoryListView,
    CategoryDetailView,
    ProductListView,
    ProductDetailView,
    UserProductView,
    UserProductDetailView,
    ProductImageListView,
    ProductImageDetailView,
    FavoriteListView,
    CartView,
    CartItemCreateView,
    CartItemDetailView,
    ChangeEMailView,
    ChangeUserNameView
)


urlpatterns = [
    # USER
    path(
        "user/register/",
        RegisterView.as_view(),
        name="register",
    ),
    path(
        "user/login/",
        LoginView.as_view(),
        name="login",
    ),
    path(
        "user/profile/",
        ProfileView.as_view(),
        name="profile",
    ),
    path(
        "user/change-password/",
        ChangePasswordView.as_view(),
        name="change-password",
    ),
    path(
        "user/change-email/",
        ChangeEMailView.as_view(),
        name="change-password",
    ),
    path(
        "user/change-username/",
        ChangeUserNameView.as_view(),
        name="change-password",
    ),

    # CATEGORIES
    path(
        "categories/",
        CategoryListView.as_view(),
        name="categories",
    ),
    path(
        "categories/<int:category_id>/",
        CategoryDetailView.as_view(),
        name="category-detail",
    ),

    # PUBLIC PRODUCTS
    path(
        "products/",
        ProductListView.as_view(),
        name="products",
    ),
    path(
        "products/<int:product_id>/",
        ProductDetailView.as_view(),
        name="product-detail",
    ),

    # USER PRODUCTS
    path(
        "user/products/",
        UserProductView.as_view(),
        name="user-products",
    ),
    path(
        "user/products/<int:product_id>/",
        UserProductDetailView.as_view(),
        name="user-product-detail",
    ),

    # PRODUCT IMAGES
    path(
        "user/products/<int:product_id>/images/",
        ProductImageListView.as_view(),
        name="product-images",
    ),
    path(
        "user/products/<int:product_id>/images/<int:image_id>/",
        ProductImageDetailView.as_view(),
        name="product-image-detail",
    ),

    # FAVORITES
    path(
        "favorites/",
        FavoriteListView.as_view(),
        name="favorites",
    ),
    path(
        "favorites/<int:product_id>/",
        FavoriteListView.as_view(),
        name="favorite-detail",
    ),

    # CART
    path(
        "cart/",
        CartView.as_view(),
        name="cart",
    ),
    path(
        "cart/items/",
        CartItemCreateView.as_view(),
        name="cart-item-create",
    ),
    path(
        "cart/items/<int:item_id>/",
        CartItemDetailView.as_view(),
        name="cart-item-detail",
    ),
]