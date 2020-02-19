from django.urls import path
from . import views

app_name = 'payment'

urlpatterns = [
    path('process/', views.process_payment, name='process'),
    path('', views.PaymentView.as_view(), name='payment'),
    path('payments_made/', views.PaymentListView.as_view(), name='payments-list'),

]