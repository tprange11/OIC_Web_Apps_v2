"""OIC_Web_Apps URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
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
from django.urls import path, include
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.HomePage.as_view(), name='home'),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('thanks/', views.ThanksPage.as_view(), name='thanks'),
    path('info/open_hockey/', views.OpenHockeyPage.as_view(), name='info-open-hockey'),
    path('info/stick_and_puck', views.StickAndPuckPage.as_view(), name='info-stick-and-puck'),
    path('web_apps/', views.WebAppsPage.as_view(), name='web_apps'),
    path('web_apps/open_hockey/', include('open_hockey.urls')),
    path('web_apps/stick_and_puck/', include('stickandpuck.urls')),
    path('web_apps/schedule/', include('schedule.urls')),
]
