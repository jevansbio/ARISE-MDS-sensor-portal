from django.apps import AppConfig


class ObservationEditorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'observation_editor'

    def ready(self):
        import observation_editor.rules  # noqa
