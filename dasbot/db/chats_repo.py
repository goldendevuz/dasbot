import logging
from datetime import datetime, timezone

from aiogram.types import Message

from dasbot.models.chat import Chat, ChatSerializer

log = logging.getLogger(__name__)


class DeleteResult:
    def __init__(self, count):
        self.deleted_count = count


class ChatsRepo(object):
    def __init__(self, chats_col, scores_col):
        self._chats = chats_col
        self._scores = scores_col
        self.__status()

    def __status(self):
        try:
            log.info("%s chat(s) in DB" % self._chats.objects.count())
            log.info("%s scores(s) in DB" % self._scores.objects.count())
        except AttributeError:
            # Fallback if mock is passed in tests
            pass

    def load_chat(self, message: Message):
        """
        :param message: Telegram message
        :return: Chat instance, loaded from DB, or new if not found
        """
        tg_chat = message.chat  # NOTE: Chat may be a group etc and have many users
        locale = message.from_user.language_code if message.from_user else None
        
        chat_model = self._chats.objects.filter(chat_id=tg_chat.id).first()
        if chat_model:
            chat_data = {
                "chat_id": chat_model.chat_id,
                "user": chat_model.user_data or {},
                "subscribed": chat_model.subscribed,
                "last_seen": chat_model.last_seen,
                "quiz": chat_model.quiz,
                "quiz_scheduled_time": chat_model.quiz_scheduled_time,
                "quiz_length": chat_model.quiz_length,
                "quiz_mode": chat_model.quiz_mode,
                "hint_language": chat_model.hint_language,
                "dictionary_level": chat_model.dictionary_level,
            }
            chat: Chat = ChatSerializer().load(chat_data)
            chat.user["last_used_locale"] = locale
        else:
            user = {
                "username": tg_chat.username,
                "first_name": tg_chat.first_name,
                "last_name": tg_chat.last_name,
                "locale": locale,
                "last_used_locale": locale,
            }
            chat = Chat(tg_chat.id, user)
        return chat

    def save_chat(self, chat: Chat, update_last_seen=False):
        if update_last_seen:
            chat.update_last_seen()
        data = ChatSerializer().dump(chat)
        defaults = {
            "user_data": data.get("user") or {},
            "subscribed": data.get("subscribed", True),
            "last_seen": data.get("last_seen"),
            "quiz": data.get("quiz"),
            "quiz_scheduled_time": data.get("quiz_scheduled_time"),
            "quiz_length": data.get("quiz_length"),
            "quiz_mode": data.get("quiz_mode"),
            "hint_language": data.get("hint_language"),
            "dictionary_level": data.get("dictionary_level"),
        }
        obj, _ = self._chats.objects.update_or_create(
            chat_id=chat.id,
            defaults=defaults
        )
        return obj

    def get_pending_chats(self, now=None):
        """
        :param now: timestamp when the function is called
        :return: list of chats that have pending quizzes
        """
        if now is None:
            now = datetime.now(tz=timezone.utc)
        results = self._chats.objects.filter(subscribed=True, quiz_scheduled_time__lte=now)
        chats = []
        for chat_model in results:
            chat_data = {
                "chat_id": chat_model.chat_id,
                "user": chat_model.user_data or {},
                "subscribed": chat_model.subscribed,
                "last_seen": chat_model.last_seen,
                "quiz": chat_model.quiz,
                "quiz_scheduled_time": chat_model.quiz_scheduled_time,
                "quiz_length": chat_model.quiz_length,
                "quiz_mode": chat_model.quiz_mode,
                "hint_language": chat_model.hint_language,
                "dictionary_level": chat_model.dictionary_level,
            }
            chats.append(ChatSerializer().load(chat_data))
        return chats

    def load_scores(self, chat_id):
        """
        :param chat_id: chat id
        :return: dict of scores {word: (score, due_date)}
        """
        results = self._scores.objects.filter(chat_id=chat_id).values_list("word", "score", "revisit")
        scores = {word: (score, revisit) for word, score, revisit in results}
        return scores

    def save_score(self, chat: Chat, word, score):
        """
        :param chat: chat instance
        :param word: word to save the score for
        :param score: a tuple (score, due_date)
        """
        obj, _ = self._scores.objects.update_or_create(
            chat_id=chat.id,
            word=word,
            defaults={"score": score[0], "revisit": score[1]}
        )
        return obj

    def delete_chat(self, chat_id):
        deleted_count, _ = self._chats.objects.filter(chat_id=chat_id).delete()
        return DeleteResult(deleted_count)

    def delete_scores(self, chat_id):
        deleted_count, _ = self._scores.objects.filter(chat_id=chat_id).delete()
        return DeleteResult(deleted_count)


if __name__ == "__main__":
    pass
