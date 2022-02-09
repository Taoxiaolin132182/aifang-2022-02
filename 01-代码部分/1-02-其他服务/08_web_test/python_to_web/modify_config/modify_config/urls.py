"""modify_config URL Configuration

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
from . import search_a1


urlpatterns = [
    path('admin/', admin.site.urls),
    path('show12/', search_a1.show_mes2),
    path('show14/', search_a1.show_mes4),
    path('index/', search_a1.index_t1),
    path('instructions/', search_a1.instructions_t1),
    path('login/', search_a1.login),
    path('do_login/', search_a1.do_login),
]
