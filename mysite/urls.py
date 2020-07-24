from django.conf.urls import include, url 
from django.contrib import admin


urlpatterns = [
	url(r'', include('login.urls')),
    url(r'^utastar/', include('utastar.urls')),
    url(r'^admin/', admin.site.urls),
]