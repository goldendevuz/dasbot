import logging
from datetime import datetime, timezone
from django.db.models import Count

from dasbot.models.chat import Chat
from dasbot import util

log = logging.getLogger(__name__)


class DeleteResult:
    def __init__(self, count):
        self.deleted_count = count


class StatsRepo(object):
    def __init__(self, scores_col, stats_col, dictionary_col_name):
        self._scores = scores_col
        self._stats = stats_col
        self._dictionary_col_name = dictionary_col_name
        self.__status()

    def __status(self):
        try:
            log.info("%s answer(s) in DB" % self._stats.objects.count())
        except AttributeError:
            pass

    def save_stats(self, chat: Chat, word, result: bool):
        """
        :param chat: chat instance
        :param word: word to save the result for
        :param result: last answer correct?
        """
        obj = self._stats.objects.create(
            chat_id=chat.id,
            word=word,
            correct=result,
            date=datetime.now(tz=timezone.utc)
        )
        return obj

    def get_stats(self, chat_id, start_date=None):
        """
        :param chat_id: chat id
        :param start_date: time when the function is called, minus 30 days
        :return: dictionary
        """
        stats = {}
        if start_date is None:
            start_date = util.month_ago()

        count = self._scores.objects.filter(chat_id=chat_id).count()
        stats['touched'] = count

        from dasbot.models.db_models import DictionaryModel

        qs = (
            self._stats.objects.filter(chat_id=chat_id, correct=False, date__gt=start_date)
            .values("word")
            .annotate(count=Count("word"))
            .filter(count__gt=1)
            .order_by("-count")[:100]
        )

        mistakes = []
        for item in qs:
            word = item["word"]
            cnt = item["count"]
            dict_entry = DictionaryModel.objects.filter(word=word).first()
            articles = dict_entry.articles if dict_entry and dict_entry.articles else "?"
            mistakes.append({"word": word, "count": cnt, "articles": articles})

        stats['mistakes_30days'] = mistakes
        return stats

    def delete_old_stats(self, cutoff_time):
        """
        :param cutoff_time: delete stats records older than this
        """
        deleted_count, _ = self._stats.objects.filter(date__lt=cutoff_time).delete()
        return DeleteResult(deleted_count)

    def delete_stats(self, chat_id):
        """
        :param chat_id: chat id to delete stats for
        """
        deleted_count, _ = self._stats.objects.filter(chat_id=chat_id).delete()
        return DeleteResult(deleted_count)


if __name__ == "__main__":
    pass
