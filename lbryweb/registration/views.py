from django.http import HttpResponseForbidden
from django.views.generic import FormView
from django.contrib.auth import login

from users.models import User
from .forms import RegistrationForm
from .daemon_plug import Account


class RegistrationView(FormView):
    template_name = 'registration.html'
    form_class = RegistrationForm
    success_url = '/'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return HttpResponseForbidden()
        else:
            return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = User.objects.create(
            username=form.cleaned_data['email'],
            email=form.cleaned_data['email']
        )
        user.set_password(form.cleaned_data['password1'])
        account = Account(user=user)
        account.register()
        user.save()
        login(self.request, user)
        return super().form_valid(form)
