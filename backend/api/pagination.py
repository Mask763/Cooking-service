from rest_framework.pagination import PageNumberPagination


class WithLimitPagination(PageNumberPagination):
    """Кастомная пагинация с лимитом."""

    page_query_param = 'page'
    page_size_query_param = 'limit'
