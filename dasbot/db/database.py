import os
import logging
import django
from django.core.management import call_command
from django.db import connection

log = logging.getLogger(__name__)


class Database(object):
    def __init__(self, settings):
        self.settings = settings
        self._models = {}

    def url(self):
        return self.settings.get("DB_ADDRESS", "postgresql://dasbot:dasbot@127.0.0.1:5432/dasbot")

    def connect(self):
        log.info("Connecting to database and initializing Django ORM: %s", self.url())
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dasbot.django_settings")
        django.setup()

        # Automatically apply migrations / create tables
        log.info("Running database schema check / migrations...")
        try:
            call_command("migrate", interactive=False, run_syncdb=True)
        except Exception as err:
            log.warning("Migration warning or error: %s", err)

        from dasbot.models.db_models import ChatModel, ScoreModel, StatModel, DictionaryModel
        from django.db import connection

        table_names = connection.introspection.table_names()
        for model in [ChatModel, ScoreModel, StatModel, DictionaryModel]:
            if model._meta.db_table not in table_names:
                try:
                    with connection.schema_editor() as schema_editor:
                        schema_editor.create_model(model)
                    table_names.append(model._meta.db_table)
                except Exception as err:
                    log.warning("Could not create model %s: %s", model, err)

        self._models = {
            "chats": ChatModel,
            "scores": ScoreModel,
            "stats": StatModel,
            "dictionary_v3": DictionaryModel,
        }
        return self

    def __getitem__(self, key):
        return self._models[key]

    def __contains__(self, key):
        return key in self._models


if __name__ == "__main__":
    pass
