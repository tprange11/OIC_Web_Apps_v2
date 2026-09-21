"""Site-level pages: home, public program info pages, the web apps landing page and
the 404/500 handlers."""
from django.views.generic import TemplateView
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from programs.models import Program

class HomePage(TemplateView):
    template_name = 'index.html'
    

class OpenHockeyPage(TemplateView):
    '''Static info page; the membership/program context it used to pull from the
    retired open_hockey app was removed with that app.'''
    template_name = 'info_open_hockey.html'


class StickAndPuckPage(TemplateView):
    template_name = 'info_stickandpuck.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['program_details'] = Program.objects.get(id=2)
        return context


class FigureSkatingPage(TemplateView):
    template_name = 'info_figure_skating.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['program_details'] = Program.objects.get(id=3)
        return context


class WebAppsPage(LoginRequiredMixin, TemplateView):
    template_name = 'web_apps.html'


class ThanksPage(TemplateView):
    template_name = 'thanks.html'


# Custom error handlers; render(None, ...) skips context processors, so the error
# pages cannot rely on request-based context such as `user` or `cart_has_items`.
def handler404(request, exception, template_name='404.html'):
    response = render(None, template_name)
    response.status_code = 404
    return response

def handler500(request, template_name='500.html'):
    response = render(None, template_name)
    response.status_code = 500
    return response
