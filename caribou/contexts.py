from django.urls import resolve

# This is required to reference the appname in Django templates
def appname(request):
    return { 'appname': resolve(request.path).app_name }


def in_group_caribou(request):
    in_group = request.user.groups.filter(name='Caribou')
    return { 'in_group_caribou': in_group }
