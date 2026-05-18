# beauty_shop\apps\common\mixins\view_mixins.py
from django.views.generic.base import ContextMixin
from apps.catalog.models import Category, Brand


class CatalogContextMixin(ContextMixin):
    """
    Agrega categorías y marcas al contexto.
    Útil para plantillas con menús o filtros laterales.
    """
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['brands'] = Brand.objects.all()
        return context


class PageTitleMixin(ContextMixin):
    """
    Permite definir un título dinámico para cada vista.
    Úsalo con 'page_title' en el contexto.
    """
    page_title = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = self.page_title or ''
        return context
