from django import forms


class ContactForm(forms.Form):
    '''Form used to send message to superusers.'''

    subject = forms.CharField(max_length=100)
    message = forms.CharField(widget=forms.Textarea)
