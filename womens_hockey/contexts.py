from django.urls import resolve

# This is required to reference the appname in Django templates
def appname(request):
    return { 'appname': resolve(request.path).app_name }


def in_group_womens_hockey(request):
    in_group = request.user.groups.filter(name='Womens Hockey')
    return { 'in_group_womens_hockey': in_group }
