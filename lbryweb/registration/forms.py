from django import forms

from users.models import User


class RegistrationForm(forms.Form):
    email = forms.EmailField(label='E-mail', max_length=100)
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput())
    password2 = forms.CharField(label='Password again', widget=forms.PasswordInput())

    def clean_email(self):
        data = self.cleaned_data['email']
        if User.objects.filter(email=data):
            raise forms.ValidationError('Enter an email that doesn\'t belong to an existing user.')
        return data

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('password1') != cleaned_data.get('password2'):
            self.add_error('password2', 'Make sure the passwords match.')
