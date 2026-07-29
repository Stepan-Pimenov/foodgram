from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path(
        'api/docs/',
        TemplateView.as_view(template_name='redoc.html'),
        name='docs',
    ),
    path(
        'api/docs/openapi-schema.yml',
        TemplateView.as_view(
            template_name='openapi-schema.yml',
            content_type='text/yaml',
        ),
        name='schema',
    ),
    path('api/', include('api.urls')),
    path('', include('recipes.urls')),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
