from django.forms import ModelForm, PasswordInput
from .models import Archive


class ArchiveForm(ModelForm):
    class Meta:
        model = Archive
        widgets = {
            'password': PasswordInput(),
        }
        exclude = []
