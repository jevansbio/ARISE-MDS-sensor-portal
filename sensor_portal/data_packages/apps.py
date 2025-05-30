from django.apps import AppConfig


class DataPackagesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'data_packages'

    def ready(self):
        import data_packages.tasks
