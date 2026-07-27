import json
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dasbot.config import settings
from dasbot.db.database import Database

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%m.%d %H:%M:%S",
)
log = logging.getLogger(__name__)


def import_dictionary(file_path):
    db = Database(settings).connect()
    DictionaryModel = db["dictionary_v3"]

    log.info("Loading dictionary from %s...", file_path)
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        entries = [{"word": w, **d} for w, d in data.items()]
    else:
        entries = data

    log.info("Importing %d entries into PostgreSQL table dictionary_v3...", len(entries))
    count = 0
    for entry in entries:
        word = entry.get("word")
        if not word:
            continue
        DictionaryModel.objects.update_or_create(
            word=word,
            defaults={
                "display_as": entry.get("display_as"),
                "articles": entry.get("articles", ""),
                "frequency": entry.get("frequency"),
                "level": entry.get("level"),
                "note": entry.get("note"),
                "translation": entry.get("translation"),
                "example": entry.get("example"),
            },
        )
        count += 1
        if count % 500 == 0:
            log.info("Imported %d entries...", count)

    log.info("Successfully imported %d entries!", count)


if __name__ == "__main__":
    dict_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dictionary", "dictionary_v3.example.json")
    if len(sys.argv) > 1:
        dict_file = sys.argv[1]
    import_dictionary(dict_file)
