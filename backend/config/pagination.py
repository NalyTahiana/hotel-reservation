from rest_framework.pagination import PageNumberPagination


class SixPerPage(PageNumberPagination):
    """Pagination de 6 éléments par page (liste publique des chambres, tableaux admin Chambres et Clients)."""

    page_size = 6
