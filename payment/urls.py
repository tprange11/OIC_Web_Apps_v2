from django.urls import path
from . import views

app_name = 'payment'

urlpatterns = [
    path('payment/', views.payment_page, name='payment'),              # Standalone card form
    path('process/', views.process_payment, name='process_payment'),   # POST target for the tokenized card
    path('payments_made/', views.PaymentListView.as_view(), name='payments_made'),
]
