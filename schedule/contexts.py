from django.urls import resolve


def appname(request):
    '''Context processor: exposes the current URL namespace as `appname` to templates.'''
    return { 'appname': resolve(request.path).app_name }