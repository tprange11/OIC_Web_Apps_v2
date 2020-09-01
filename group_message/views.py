from django.shortcuts import reverse
from django.views.generic import FormView
from django.contrib.auth.models import Group
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core.mail import send_mass_mail

from .forms import GroupMessageForm


class GroupMessageView(LoginRequiredMixin, FormView):
    '''Displays page where superusers and group managers can send an email 
    message to the respective group.'''

    template_name = 'group_message_form.html'
    form_class = GroupMessageForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group_id = self.kwargs['group']
        context['group_name'] = Group.objects.get(id=group_id).name
        return context
        

    def get_initial(self):
        initial = super().get_initial()
        # Get group id from url to send to correct group
        if self.request.method == 'GET':
            initial['group'] = self.kwargs['group']
        return initial

    def form_valid(self, form):
        group = Group.objects.get(id=form.cleaned_data.get('group'))
        recipients = group.user_set.all().values_list('email', flat=True)
        subject = form.cleaned_data.get('subject')
        message = form.cleaned_data.get('message')
        from_email = self.request.user.email
        group_email = (subject, message, from_email, recipients)

        try:
            send_mass_mail((group_email, ))
            messages.add_message(self.request, messages.INFO, 'Your message was successfully sent to the group!')
            self.success_url = reverse('group_message:group-message', kwargs={'group': form.cleaned_data.get('group')})
        except:
            messages.add_message(self.request, messages.ERROR, 'Something went wrong, please try again!')
            return reverse('group_message:group-message', kwargs={'group': form.cleaned_data.get('group')})
        return super().form_valid(form)
