
from django.contrib import admin

from .models import Cart, CartItem, Category, Favorite, Product, ProductImage


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "user",
        "price",
        "stock",
        "is_active",
        "is_featured",
        "created_at",
    )

    list_filter = (
        "is_active",
        "is_featured",
        "category",
        "created_at",
    )

    list_editable = (
        "is_active",
        "is_featured",
    )

    search_fields = (
        "title",
        "description",
        "user__username",
    )

    list_per_page = 25


admin.site.register(Category)
admin.site.register(ProductImage)
admin.site.register(Favorite)
admin.site.register(Cart)
admin.site.register(CartItem)
