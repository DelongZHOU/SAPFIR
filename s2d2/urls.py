from django.conf.urls import  include, url
from django.urls import path

from django.contrib import admin
#from splee import urls as splee_urls

from s2d2 import views
from django.conf import settings
from django.conf.urls.static import static


admin.autodiscover()

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^splee/', include('splee.urls')),
    path('',views.home, name='home'),
    url(r'^home/',views.home, name='home'),
    url(r'^help/',views.help, name='help'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) #this line allows the download via filefield.url
