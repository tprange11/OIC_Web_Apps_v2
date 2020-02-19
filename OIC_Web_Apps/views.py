from django.views.generic import TemplateView
from open_hockey.models import OpenHockeyMemberType

class HomePage(TemplateView):
    template_name = 'index.html'
    
class OpenHockeyPage(TemplateView):
    template_name = 'info_open_hockey.html'
    model = OpenHockeyMemberType

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        member_types = self.model.objects.all()
        context['memberships'] = member_types
        return context

class StickAndPuckPage(TemplateView):
    template_name = 'info_stickandpuck.html'

class WebAppsPage(TemplateView):
    template_name = 'web_apps.html'

class ThanksPage(TemplateView):
    template_name = 'thanks.html'
