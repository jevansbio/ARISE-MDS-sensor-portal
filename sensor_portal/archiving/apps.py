from django.apps import AppConfig


class ArchivingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'archiving'

    def ready(self):
        # Make sure that signals and tasks are loaded
        import archiving.tasks
