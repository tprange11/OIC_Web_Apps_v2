from django.urls import path
from . import views

app_name = 'figure_skating'

urlpatterns = [
    path('', views.FigureSkatingView.as_view(), name='figure-skating'),
    path('add_skater/', views.CreateFigureSkaterView.as_view(), name='add-skater'),
    path('remove_skater/<pk>', views.DeleteFigureSkaterView.as_view(), name='remove-skater'),
    path('sessions/register/<session>/', views.CreateFigureSkatingSessionView.as_view(), name='session-register'),
    path('session/register/', views.CreateFigureSkatingSessionView.as_view(), name='session-register'),
    path('session/remove/<pk>', views.DeleteFigureSkatingSessionView.as_view(), name='session-remove'),
    
]
