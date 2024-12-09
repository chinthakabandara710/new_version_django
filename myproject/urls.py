from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

def empty_favicon(request):
    return HttpResponse('', content_type='image/x-icon')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('myapp.urls')),
    path('favicon.ico', empty_favicon),
] + static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
