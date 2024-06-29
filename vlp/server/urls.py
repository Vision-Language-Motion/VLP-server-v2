from django.urls import include, path
from rest_framework import routers
from django.conf.urls.static import static
from . import settings
from django.views.generic.base import TemplateView 

from api import views

router = routers.DefaultRouter()
router.register(r'videos', views.VideoViewSet)

# (commented out) Wire up our API using automatic URL routing.
# (commented out) Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path('', include(router.urls)),
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
    path('upload/', views.upload_file, name='upload_file'),
#     path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)