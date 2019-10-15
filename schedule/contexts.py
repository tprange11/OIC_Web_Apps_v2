from django.urls import resolve

# This is required to reference the appname in Django Templates
def appname(request):
    return { 'appname': resolve(request.path).app_name }