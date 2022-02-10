from django.urls import resolve

# This is required to reference the appname in Django templates
def appname(request):
    return { 'appname': resolve(request.path).app_name }


def in_group_nacho_skate(request):
    in_group = request.user.groups.filter(name='Nacho Skate')
    return { 'in_group_nacho_skate': in_group }
