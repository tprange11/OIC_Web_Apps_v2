from django.urls import path, include
from . import views

app_name = 'schedule'

urlpatterns = [
    path('', views.ChooseRink.as_view(), name='choose-rink'),
    path('api/', views.RinkScheduleListAPIView.as_view()),
    path('rink/<rink>', views.RinkScheduleListView.as_view(), name='rink-schedule-list'),
    path('rink/', views.RinkScheduleListView.as_view(), name='rink-schedule-list'),
    path('rink/update_schedule/', views.scrape_schedule, name='update-schedule'),
]

urlpatterns += [
    path("runs/", views.run_list, name="schedule_run_list"),
    path("runs/<int:run_id>/", views.run_detail, name="schedule_run_detail"),
    path(
        "diff/<int:run_a>/<int:run_b>/",
        views.run_diff,
        name="schedule_run_diff",
    ),
]