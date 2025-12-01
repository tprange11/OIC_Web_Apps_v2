from django.urls import path
from . import views

app_name = 'payment'

urlpatterns = [
    path('payment/', views.payment_page, name='payment'),              # Shows the payment form
    path('process/', views.process_payment, name='process_payment'),   # Handles POST from JS
    path('payments_made/', views.PaymentListView.as_view(), name='payments_made'),
]
