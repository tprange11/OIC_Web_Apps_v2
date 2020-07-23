from django.db import models


class Program(models.Model):
    '''Model holds details for OIC skating programs.'''

    # Model Fields
    program_name = models.CharField(max_length=100, unique=True)
    max_skaters = models.IntegerField(blank=True, null=True, default=22)
    max_goalies = models.IntegerField(blank=True, null=True)
    skater_price = models.IntegerField(blank=True, null=True)
    goalie_price = models.IntegerField(blank=True, null=True)

    class Meta:
        ordering = ['pk']

    def __str__(self):
        return f'{ self.program_name }'


class UserCreditIncentive(models.Model):
    '''Model that holds price point incentives for purchasing User Credits.
    These apply to the accounts/UserCredit model.'''

    # Model Fields
    price_point = models.PositiveSmallIntegerField(help_text='The price at which the incentive kicks in.', null=False, blank=False)
    incentive = models.PositiveSmallIntegerField(help_text='Percentage of free credits for this price point. Enter as whole number.', null=False, blank=False)

    class Meta:
        ordering = ['-price_point']

    def __str__(self):
        return f'At ${self.price_point}, {self.incentive}% will be added to credits purchased.'
