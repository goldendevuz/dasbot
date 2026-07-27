import logging
from datetime import datetime
from pytz import timezone

from rest_framework import serializers

from dasbot import util
from dasbot.models.quiz import QuizMode, QuizSerializer
from dasbot.models.dictionary import Level
from dasbot.config import settings

log = logging.getLogger(__name__)


class Chat(object):
    def __init__(self, chat_id, user={}, subscribed=True, last_seen=None, quiz=None,
                 quiz_scheduled_time=None, quiz_length=None, quiz_mode=None, hint_language=None, dictionary_level=None):
        self.id = chat_id
        self.user = user
        self.subscribed = subscribed
        self.last_seen = last_seen
        self.quiz = quiz
        self.quiz_scheduled_time = quiz_scheduled_time
        self.quiz_length = quiz_length or settings.QUIZ_LENGTH
        self.quiz_mode = quiz_mode or QuizMode.Advance
        self.dictionary_level = dictionary_level or Level.Default
        if self.quiz_scheduled_time is None:
            self.quiz_scheduled_time = util.next_quiz_time(datetime.now(tz=timezone('UTC')))
        self.hint_language = hint_language or None

    def update_last_seen(self):
        self.last_seen = datetime.now(tz=timezone('UTC'))

    def unsubscribe(self):
        self.subscribed = False

    def subscribe(self):
        self.subscribed = True

    def set_quiz_time(self, hhmm, skip_today=False):
        """
        :param hhmm: string "HH:MM"
        :param skip_today: skip nearest HH:MM if today
        :return: nothing, changes the Chat instance
        """
        berlin = timezone('Europe/Berlin')
        now = datetime.now().astimezone(berlin)
        self.quiz_scheduled_time = util.next_hhmm(hhmm, now, skip_today=skip_today)


class UserSerializer(serializers.Serializer):
    username = serializers.CharField(required=False, allow_null=True, default=None)
    first_name = serializers.CharField(required=False, allow_null=True, default=None)
    last_name = serializers.CharField(required=False, allow_null=True, default=None)
    locale = serializers.CharField(required=False, allow_null=True, default=None)
    last_used_locale = serializers.CharField(required=False, allow_null=True, default=None)

    def to_internal_value(self, data):
        known_fields = {field: data[field] for field in self.fields if field in data}
        return super().to_internal_value(known_fields)


class ChatSerializer(serializers.Serializer):
    chat_id = serializers.IntegerField(source='id')
    user = UserSerializer(required=False, default=dict)
    subscribed = serializers.BooleanField(required=False, default=True)
    last_seen = serializers.DateTimeField(required=False, allow_null=True, default=None)
    quiz = QuizSerializer(required=False, allow_null=True, default=None)
    quiz_scheduled_time = serializers.DateTimeField(required=False, allow_null=True, default=None)
    quiz_length = serializers.IntegerField(required=False, allow_null=True, default=None)
    quiz_mode = serializers.ChoiceField(choices=[m.value for m in QuizMode], required=False, allow_null=True, default=None)
    hint_language = serializers.CharField(required=False, allow_null=True, default=None)
    dictionary_level = serializers.ChoiceField(choices=[l.value for l in Level], required=False, allow_null=True, default=None)

    def to_internal_value(self, data):
        known_fields = {field: data[field] for field in self.fields if field in data}
        return super().to_internal_value(known_fields)

    def create(self, validated_data):
        chat_id = validated_data.pop('id', None) or validated_data.pop('chat_id', None)
        if 'quiz_mode' in validated_data and validated_data['quiz_mode']:
            if not isinstance(validated_data['quiz_mode'], QuizMode):
                validated_data['quiz_mode'] = QuizMode(validated_data['quiz_mode'])
        if 'dictionary_level' in validated_data and validated_data['dictionary_level']:
            if not isinstance(validated_data['dictionary_level'], Level):
                validated_data['dictionary_level'] = Level.from_value(validated_data['dictionary_level'])
        if 'quiz' in validated_data and isinstance(validated_data['quiz'], dict):
            validated_data['quiz'] = QuizSerializer().create(validated_data['quiz'])
        return Chat(chat_id=chat_id, **validated_data)

    def update(self, instance, validated_data):
        return self.create(validated_data)

    def dump(self, instance):
        return ChatSerializer(instance).data

    def load(self, data, **kwargs):
        serializer = ChatSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return serializer.save()


# Backward compatibility aliases
UserSchema = UserSerializer
ChatSchema = ChatSerializer

if __name__ == "__main__":
    pass
