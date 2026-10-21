from django.contrib import admin

from .models import Cart, CartItem, Category, Favorite, Product, ProductImage


admin.site.register(Category)
admin.site.register(Product)
admin.site.register(ProductImage)
admin.site.register(Favorite)
admin.site.register(Cart)
admin.site.register(CartItem)