from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()


class Payment(models.Model):
    '''One completed Square payment. `note` is the "(Program $amount) ..." breakdown
    built in payment/views.py and parsed by the revenue reports.'''

    payer = models.ForeignKey(User, on_delete=models.CASCADE)
    square_id = models.CharField(max_length=200)
    square_receipt = models.CharField(max_length=100, null=True, blank=True)
    amount = models.FloatField()
    note = models.CharField(max_length=200)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.payer.first_name} {self.payer.last_name} > Paid: ${self.amount} > Date: {self.date}"

    class Meta:
        ordering = ['-date']


class PaymentError(models.Model):
    '''A Square error returned while processing a payment, kept for support.'''

    payer = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    error = models.TextField()
