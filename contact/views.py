from django.shortcuts import render, reverse
from django.views.generic import FormView
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core.mail import send_mail

from .forms import ContactForm


class ContactFormView(LoginRequiredMixin, FormView):
    '''Displays contact page where users can submit a message to all superusers.'''

    template_name = 'contact_form.html'
    form_class = ContactForm

    def form_valid(self, form):
        recipients = User.objects.filter(id__in=['1', '2']).values_list('email', flat=True)
        subject = form.cleaned_data.get('subject')
        subject += ' - oicwebapps.com'
        name = self.request.user.get_full_name()
        message = f'Message from {name}\n\n'
        message += f'##########################################################################\n\n'
        message += form.cleaned_data.get('message')
        from_email = self.request.user.email

        try:
            #send_mail(subject, message, from_email, recipients)
            messages.add_message(self.request, messages.INFO, 'Your message has been sent! Someone will contact you shortly.')
            self.success_url = reverse('contact:contact-form')
        except:
            messages.add_message(self.request, messages.ERROR, 'Oops, something went wrong!  Please try again.')
            return reverse('contact:contact-form', kwargs={ 'form': form.cleaned_data })

        return super().form_valid(form)
