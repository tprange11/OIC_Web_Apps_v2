from django import forms
from .models import Topic, Post


class CreateBoardTopicForm(forms.ModelForm):
    '''Form used to create a new board topic.'''

    message = forms.CharField(widget=forms.Textarea(), max_length=4000)

    class Meta:
        model = Topic
        fields = ['subject', 'message', 'sticky']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['subject'].widget.attrs['placeholder'] = ('Max length 50 characters')
        self.fields['message'].widget.attrs['placeholder'] = ('Max length 4000 characters')


class CreateBoardTopicPostReplyForm(forms.ModelForm):
    '''Form used to create a reply post to a topic.'''

    class Meta:
        model = Post
        fields = ['message']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['message'].widget.attrs['placeholder'] = ('Max length 4000 characters')


class PostUpdateForm(forms.ModelForm):
    '''Form used to update a users post.'''

    class Meta:
        model = Post
        fields = ['message']
