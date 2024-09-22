from rest_framework.pagination import PageNumberPagination


class WithLimitPagination(PageNumberPagination):
    """Кастомная пагинация с лимитом."""

    page_size_query_param = 'limit'
    page_size = 6
