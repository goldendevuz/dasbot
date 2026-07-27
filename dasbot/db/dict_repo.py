import logging
from collections import defaultdict

from dasbot.models.dictionary import Dictionary, DictionaryEntrySerializer, Level

log = logging.getLogger(__name__)


class DictRepo(object):
    def __init__(self, dict_col):
        self._dict_col = dict_col

    def load(self):
        """
        :return: defaultdict of Level -> Dictionary, with full dictionary as default
        """
        data_cursor = self._dict_col.objects.all()
        dict_data = {}
        for item in data_cursor:
            item_dict = {
                "word": item.word,
                "display_as": item.display_as,
                "articles": item.articles,
                "frequency": item.frequency,
                "level": item.level,
                "note": item.note,
                "translation": item.translation,
                "example": item.example,
            }
            dict_data.update(DictionaryEntrySerializer().load(item_dict))

        log.info("%s dictionary word(s) in DB", len(dict_data))
        if len(dict_data) == 0:
            log.warning("Dictionary is empty")

        dictionaries = defaultdict(lambda: Dictionary(dict_data))
        for level in Level:
            if level == Level.Default:
                dictionaries[level] = Dictionary(dict_data)
            else:
                dictionaries[level] = Dictionary(self.filter_by_level(dict_data, level))
        return dictionaries

    def filter_by_level(self, data, level):
        return {
            word: val
            for word, val in data.items()
            if (val.get("level") or "").lower() == level.value.lower()
        }


if __name__ == "__main__":
    pass
