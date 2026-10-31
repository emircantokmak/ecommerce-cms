import django_filters

from .models import Product


class ProductFilter(django_filters.FilterSet):

    search = django_filters.CharFilter(
        method="filter_search"
    )

    category = django_filters.CharFilter(
        field_name="category__slug",
        lookup_expr="iexact"
    )

    min_price = django_filters.NumberFilter(
        field_name="price",
        lookup_expr="gte"
    )

    max_price = django_filters.NumberFilter(
        field_name="price",
        lookup_expr="lte"
    )

    class Meta:
        model = Product
        fields = [
            "category",
            "min_price",
            "max_price",
        ]

    def filter_search(self, queryset, name, value):

        return queryset.filter(
            title__icontains=value
        ) | queryset.filter(
            description__icontains=value
        )