"""use_web1215 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from . import views_try, search, search2
from django.conf.urls import url

urlpatterns = [
    path('', views_try.hello),
    path('fun1/', views_try.fun1),
    path('runoob/', views_try.runoob),
    path('runoob/', views_try.runoob2),
    path('cainiao1/', views_try.cainiao1),
    path('show1/', search2.show_mes1),
    path('show2/', search2.show_mes2),
    url(r'^search-form/$', search.search_form),
    url(r'^search/$', search.search),
    url(r'^search-post/$', search2.search_post),

]
# urlpatterns = [
#     path('admin/', admin.site.urls),
# ]
# path('search-form/', search.search_form),
#     path('search/', search.search),