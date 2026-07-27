import logging
from enum import Enum
from rest_framework import serializers

log = logging.getLogger(__name__)

class Level(Enum):
    Default = 'default'
    A1 = 'a1'
    A2 = 'a2'
    B1 = 'b1'
    B2 = 'b2'
    C1 = 'c1'

    @classmethod
    def from_value(cls, value):
        return next((m for m in cls if m.value == value), Level.Default)


class Dictionary(object):
    """
    Dictionary

    Args:
        dict_data (dict): see DictionaryEntrySerializer for structure }
    """

    def __init__(self, dict_data):
        self._contents = dict_data
        self._words = self._contents.keys()

    def words(self):
        """Returns (a set-like view of) all words, in insertion order"""
        # NOTE: use list() to make a copy of the set
        return self._words

    def wordcount(self):
        """Returns the dictionary length"""
        return len(self._words)

    def articles(self, word) -> str | None:
        """Returns the article(s) string for specified word (separated by '/' if more than one)"""
        return self._contents.get(word, {}).get("articles")

    def display_as(self, word) -> str:
        """Returns the display_as string for specified word"""
        return self._contents.get(word, {}).get("display_as") or word

    def note(self, word) -> str | None:
        """Returns the comment in German"""
        return self._contents.get(word, {}).get("note")

    def translation(self, word, locale) -> str | None:
        """Returns the translation for specified word and locale"""
        return self._contents.get(word, {}).get("translation", {}).get(locale)

    def frequency(self, word) -> float:
        """Returns the word's frequency"""
        return self._contents.get(word, {}).get("frequency", 0.0)

    def level(self, word) -> str | None:
        """Returns the word's level"""
        return self._contents.get(word, {}).get("level")

    def example(self, word)  -> str | None:
        """Returns the example sentence for specified word"""
        return self._contents.get(word, {}).get("example")

    def has(self, word) -> bool:
        """Returns True if word is in dictionary"""
        return self._contents.get(word) is not None


class DictionaryEntrySerializer(serializers.Serializer):
    word = serializers.CharField()
    display_as = serializers.CharField(required=False, allow_null=True, allow_blank=True, default=None)
    articles = serializers.CharField()
    frequency = serializers.FloatField(required=False, allow_null=True, default=None)
    level = serializers.CharField(required=False, allow_null=True, allow_blank=True, default=None)
    note = serializers.CharField(required=False, allow_null=True, allow_blank=True, default=None)
    translation = serializers.DictField(child=serializers.CharField(allow_null=True, allow_blank=True), required=False, allow_null=True, default=None)
    example = serializers.CharField(required=False, allow_null=True, allow_blank=True, default=None)

    def to_internal_value(self, data):
        known_fields = {field: data[field] for field in self.fields if field in data}
        return super().to_internal_value(known_fields)

    def create(self, validated_data):
        return {
            validated_data["word"]: {
                "articles": validated_data["articles"],
                "display_as": validated_data.get("display_as"),
                "level": validated_data.get("level"),
                "frequency": validated_data.get("frequency"),
                "note": validated_data.get("note"),
                "translation": validated_data.get("translation"),
                "example": validated_data.get("example"),
            }
        }

    def update(self, instance, validated_data):
        return self.create(validated_data)

    def dump(self, instance):
        return DictionaryEntrySerializer(instance).data

    def load(self, data, **kwargs):
        serializer = DictionaryEntrySerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return serializer.save()


# Backward compatibility alias
DictionaryEntrySchema = DictionaryEntrySerializer

if __name__ == "__main__":
    pass
