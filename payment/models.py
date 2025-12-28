from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()

# Create your models here.

class Payment(models.Model):
    '''Payment Model holds payment records.'''

    # Model fields
    payer = models.ForeignKey(User, on_delete=models.CASCADE)
    square_id = models.CharField(max_length=200)
    square_receipt = models.CharField(max_length=100)
    amount = models.FloatField()
    note = models.CharField(max_length=200)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.payer.first_name} {self.payer.last_name} > Paid: ${self.amount} > Date: {self.date}"

    class Meta:
        ordering = ['-date']


class PaymentError(models.Model):
    '''Model holds any payment errors received.'''

    # Model Fields
    payer = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    error = models.TextField()
