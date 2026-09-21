from django.db import models


class Program(models.Model):
    '''One row per skating program (Stick and Puck, Figure Skating, ...).

    Other apps look programs up by hard-coded id (cart/views.py, OIC_Web_Apps/views.py)
    and by program_name (cart items, payment notes), so neither should be edited casually.
    Skater/goalie limits and prices here are the defaults the program apps enforce.'''

    program_name = models.CharField(max_length=100, unique=True)
    description = models.TextField(
        null=True, 
        blank=True, 
        max_length=400,
        help_text='Max 400 characters'
    )
    message = models.CharField(
        max_length=200, 
        blank=True, 
        null=True, 
        help_text='Used for special messages, will be displayed as bold in colored info box.'
        )
    days_and_times = models.CharField(max_length=100, default='Check OICWebApps for days/times')
    private = models.BooleanField(default=False, help_text='If checked, this program will not be shown to the public.')
    max_skaters = models.IntegerField(blank=True, null=True, default=22)
    max_goalies = models.IntegerField(blank=True, null=True)
    skater_price = models.IntegerField(blank=True, null=True)
    goalie_price = models.IntegerField(blank=True, null=True)

    class Meta:
        ordering = ['pk']

    def __str__(self):
        return f'{ self.program_name }'


class UserCreditIncentive(models.Model):
    '''Bonus tiers for User Credit purchases: buying at least `price_point` dollars
    adds `incentive` percent extra credits (see accounts.views.UpdateUserCreditView).
    Ordered highest tier first, which that view relies on.'''

    price_point = models.PositiveSmallIntegerField(help_text='The price at which the incentive kicks in.', null=False, blank=False)
    incentive = models.PositiveSmallIntegerField(help_text='Percentage of free credits for this price point. Enter as whole number.', null=False, blank=False)

    class Meta:
        ordering = ['-price_point']

    def __str__(self):
        return f'At ${self.price_point}, {self.incentive}% will be added to credits purchased.'
