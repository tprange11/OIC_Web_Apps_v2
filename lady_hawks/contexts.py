from django.urls import resolve

# This is required to reference the appname in Django templates
def appname(request):
    return { 'appname': resolve(request.path).app_name }


def in_group_lady_hawks(request):
    in_group = request.user.groups.filter(name='Lady Hawks')
    return { 'in_group_lady_hawks': in_group }
