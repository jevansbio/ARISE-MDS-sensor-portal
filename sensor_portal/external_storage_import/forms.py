from django.forms import ModelForm, PasswordInput
from .models import DataStorageInput


class DataStorageInputForm(ModelForm):
    class Meta:
        model = DataStorageInput
        widgets = {
            'password': PasswordInput(),
        }
        exclude = []
