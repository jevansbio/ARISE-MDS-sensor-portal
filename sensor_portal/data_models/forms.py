from django.forms import ModelForm, PasswordInput
from .models import Device


class DeviceForm(ModelForm):
    class Meta:
        model = Device
        widgets = {
            'password': PasswordInput(),
        }
        exclude = []
