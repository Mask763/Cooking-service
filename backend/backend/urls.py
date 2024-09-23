from django.contrib import admin
from django.urls import include, path, re_path

from recipes.views import short_link_redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    re_path(
        r'^(?P<short_link>[a-zA-Z0-9]{10})/$',
        short_link_redirect,
        name='recipe_redirect'
    ),
]
