from django.views.generic import TemplateView
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
# from open_hockey.models import OpenHockeyMemberType
from programs.models import Program

class HomePage(TemplateView):
    template_name = 'index.html'
    

class OpenHockeyPage(TemplateView):
    template_name = 'info_open_hockey.html'
    # model = OpenHockeyMemberType

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     member_types = self.model.objects.all()
    #     context['memberships'] = member_types
    #     context['program_details'] = Program.objects.get(id=1)
    #     return context


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


def handler404(request, exception, template_name='404.html'):
    response = render(None, template_name)
    response.status_code = 404
    return response

def handler500(request, template_name='500.html'):
    response = render(None, template_name)
    response.status_code = 500
    return response
