from django.urls import resolve

# Context processor: lets templates check whether the user is in the CHS Alumni group
def in_group_chs_alumni(request):
    in_group = request.user.groups.filter(name='CHS Alumni')
    return { 'in_group_chs_alumni': in_group }
