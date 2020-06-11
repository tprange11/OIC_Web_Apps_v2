from django.urls import resolve

# This is required to reference the appname in Django templates
def appname(request):
    return { 'appname': resolve(request.path).app_name }


def in_group_mike_schultz(request):
    in_group = request.user.groups.filter(name='Mike Schultz')
    return { 'in_group_mike_schultz': in_group }
