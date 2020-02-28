from django.urls import resolve

# This is required to reference the appname in Django templates
def appname(request):
    return { 'appname': resolve(request.path).app_name }

def in_group_thane_storck(request):
    in_group = request.user.groups.filter(name='Thane Storck').exists()
    return {'in_group_thane_storck': in_group}
