from django.contrib import admin
from . import models

# Register your models here.

class PaymentAdmin(admin.ModelAdmin):
    # readonly_fields = ('payer', 'square_id', 'square_receipt', 'amount', 'note', 'date',)
    list_display = ['payer_name', 'dollar_amount', 'note', 'date']
    search_fields = ['payer__first_name', 'payer__last_name', 'note', 'date']

    def payer_name(self, obj):
        return f"{obj.payer.first_name} {obj.payer.last_name}"

    def dollar_amount(self, obj):
        return f"${obj.amount}"


class PaymentErrorAdmin(admin.ModelAdmin):
    readonly_fields = ['payer', 'error', 'date']
    list_display = ['payer_name', 'date', 'error']

    def payer_name(self, obj):
        return f"{obj.payer.first_name} {obj.payer.last_name}"


admin.site.register(models.Payment, PaymentAdmin)
admin.site.register(models.PaymentError, PaymentErrorAdmin)
