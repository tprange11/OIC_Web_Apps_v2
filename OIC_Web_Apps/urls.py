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
from django.views.generic import TemplateView

handler404 = 'OIC_Web_Apps.views.handler404'
handler500 = 'OIC_Web_Apps.views.handler500'

def trigger_error(request):
    '''Used for testing Sentry SDK'''
    division_by_zero = 1 / 0

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.HomePage.as_view(), name='home'),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('thanks/', views.ThanksPage.as_view(), name='thanks'),
    path('info/open_hockey/', views.OpenHockeyPage.as_view(),
         name='info-open-hockey'),
    path('info/stick_and_puck/', views.StickAndPuckPage.as_view(),
         name='info-stick-and-puck'),
    path('info/figure_skating/', views.FigureSkatingPage.as_view(),
         name='info-figure-skating'),
    path('group_message/', include('group_message.urls')),
    path('message_boards/', include('message_boards.urls')),
    path('payment/', include('payment.urls')),
    path('web_apps/thane_storck/', include('thane_storck.urls')),
    path('web_apps/', views.WebAppsPage.as_view(), name='web_apps'),
    path('web_apps/shopping_cart/', include('cart.urls')),
    # path('web_apps/open_hockey/', include('open_hockey.urls')),
    path('web_apps/stick_and_puck/', include('stickandpuck.urls')),
    path('web_apps/adult_skills/', include('adult_skills.urls')),
    path('web_apps/mike_schultz/', include('mike_schultz.urls')),
    path('web_apps/yeti_skate/', include('yeti_skate.urls')),
    path('web_apps/womens_hockey/', include('womens_hockey.urls')),
    path('web_apps/bald_eagles/', include('bald_eagles.urls')),
    path('web_apps/lady_hawks/', include('lady_hawks.urls')),
    path('web_apps/schedule/', include('schedule.urls')),
    path('serviceworker.js', (TemplateView.as_view(
        template_name='serviceworker.js',
        content_type='application/javascript'
    )), name='serviceworker.js'),
    path('offline/', (TemplateView.as_view(template_name='offline.html',
                                           content_type='text/html')), name='offline'),
    path('web_apps/figure_skating/', include('figure_skating.urls')),
    path('sentry_debug/', trigger_error),
    path('500/', views.handler500),
]
