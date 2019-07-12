from django.conf.urls import url
from rest_framework.routers import DefaultRouter

from . import views


urlpatterns = [
    url(r'^categories/(?P<category_id>\d+)/skus', views.SKUListView.as_view())
]

route = DefaultRouter()
route.register('skus/search', views.SKUSearchViewSet, base_name='sku_search')

urlpatterns += route.urls