from django import forms


class GroupMessageForm(forms.Form):
    '''Form used to send group messages.'''

    group = forms.CharField(widget=forms.HiddenInput())
    subject = forms.CharField(max_length=50)
    message = forms.CharField(widget=forms.Textarea())

    def __init__(self, *args, **kwargs):
        super(GroupMessageForm, self).__init__(*args, **kwargs)
        self.fields['subject'].widget.attrs['placeholder'] = ('50 Chars Max')
        self.fields['message'].widget.attrs['placeholder'] = ('Type your message here')
