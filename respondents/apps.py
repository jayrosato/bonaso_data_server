from django.apps import AppConfig


class RespondentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'respondents'
    def ready(self):
        import respondents.signals
