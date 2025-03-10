from django.db import models


class BaseModel(models.Model):
    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def model_name(self):
        return self._meta.model_name

    def save(self, *args, **kwargs):
        self.clean()
        return super().save(*args, **kwargs)
