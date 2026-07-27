from django.db import models


class ChatModel(models.Model):
    chat_id = models.BigIntegerField(primary_key=True)
    user_data = models.JSONField(default=dict, null=True, blank=True)
    subscribed = models.BooleanField(default=True)
    last_seen = models.DateTimeField(null=True, blank=True)
    quiz = models.JSONField(null=True, blank=True)
    quiz_scheduled_time = models.DateTimeField(null=True, blank=True, db_index=True)
    quiz_length = models.IntegerField(null=True, blank=True)
    quiz_mode = models.CharField(max_length=32, null=True, blank=True)
    hint_language = models.CharField(max_length=32, null=True, blank=True)
    dictionary_level = models.CharField(max_length=32, null=True, blank=True)

    class Meta:
        db_table = "chats"


class ScoreModel(models.Model):
    chat_id = models.BigIntegerField(db_index=True)
    word = models.CharField(max_length=255)
    score = models.IntegerField(default=0)
    revisit = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "scores"
        unique_together = [("chat_id", "word")]


class StatModel(models.Model):
    chat_id = models.BigIntegerField(db_index=True)
    word = models.CharField(max_length=255, db_index=True)
    correct = models.BooleanField()
    date = models.DateTimeField(db_index=True)

    class Meta:
        db_table = "stats"


class DictionaryModel(models.Model):
    word = models.CharField(max_length=255, primary_key=True)
    display_as = models.CharField(max_length=255, null=True, blank=True)
    articles = models.CharField(max_length=255)
    frequency = models.FloatField(null=True, blank=True)
    level = models.CharField(max_length=32, null=True, blank=True)
    note = models.TextField(null=True, blank=True)
    translation = models.JSONField(null=True, blank=True)
    example = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "dictionary_v3"
