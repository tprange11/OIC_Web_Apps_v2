from django.views.generic import TemplateView

class HomePage(TemplateView):
    template_name = 'index.html'
    
class OpenHockeyPage(TemplateView):
    template_name = 'info_open_hockey.html'

class StickAndPuckPage(TemplateView):
    template_name = 'info_stickandpuck.html'

class WebAppsPage(TemplateView):
    template_name = 'web_apps.html'

class ThanksPage(TemplateView):
    template_name = 'thanks.html'