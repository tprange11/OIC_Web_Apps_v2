from .models import Cart
from django.contrib.auth.decorators import login_required


# If the cart has items return True, else return False
# @login_required
def cart_has_items(request):
    model = Cart
    if request.user.is_anonymous:
        return {'cart_has_items': False}
    else:
        queryset = model.objects.filter(customer=request.user)
        if queryset:
            return {'cart_has_items': True}
        else:
            return {'cart_has_items': False}
