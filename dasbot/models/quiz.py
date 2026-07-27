import logging
from datetime import datetime, timedelta
from random import shuffle
from typing import Tuple
from enum import Enum
from pytz import timezone

from rest_framework import serializers

from dasbot.models.dictionary import Dictionary
from dasbot.types import Scores, Words, Cards
from dasbot.util import equalizer

log = logging.getLogger(__name__)


# Spaced repetition schedule
SCHEDULE = {
    0: timedelta(0),
    1: timedelta(hours=1),
    2: timedelta(days=1),
    3: timedelta(weeks=1),
    4: timedelta(weeks=4),
    5: timedelta(weeks=12),
    6: timedelta(weeks=24)
}

# 50/50 review + new words or maximize review
class QuizMode(Enum):
    Advance = 'advance'
    Review = 'review'

class Quiz(object):
    def __init__(self, cards=[], position=0, correctly=0, active=False, scores={}):
        self.cards = cards
        self.position = position
        self.correctly = correctly
        self.active = active
        self.scores = scores
        self.length = len(cards)

    @staticmethod
    def new(length: int, scores: Scores, dictionary: Dictionary, mode: QuizMode):
        """ Returns a new fully prepared Quiz
        :param scores: dictionary {word: (score, due_date)}
        :return: new Quiz instance
        """
        review_scores = Quiz.get_review(scores, length, dictionary)
        new_words = Quiz.get_new_words(scores, length, dictionary)
        cards, selected_scores = Quiz.make_cards(length, review_scores, new_words, dictionary, mode)

        #TODO: Preferably, store review_scores with cards (requires DB migration)
        return Quiz(
            cards=cards,
            position=0,
            correctly=0,
            active=True,
            scores=selected_scores
        )

    @staticmethod
    def get_new_words(scores: Scores, max_num: int, dictionary: Dictionary) -> Words:
        """ Selects from the dictionary words which have not been seen yet
            Returns max_num (or fewer) words
        """
        all_new_words = dictionary.words() - scores.keys()
        all_sorted = sorted(all_new_words, key=lambda k: -dictionary.frequency(k))
        count = min(len(all_new_words), max_num)
        new_words = [v for _, v in zip(range(count), all_sorted)]
        return new_words

    @staticmethod
    def get_review(scores: Scores, max_len: int, dictionary: Dictionary, now=None) -> Scores:
        """ Selects overdue words to practice from the history dict
        :param scores: dictionary {word: (score, due_date)}
        :param max_len: integer; function returns this (or fewer) entries
        :param now: datetime for testing
        :return: review (overdue scores), in the same format as input dictionary
        """
        if now is None:
            now = datetime.now(tz=timezone('UTC'))

        def is_overdue(due_date):
            if not due_date:
                return False
            dt_now = now
            if dt_now.tzinfo and due_date.tzinfo is None:
                due_date = due_date.replace(tzinfo=timezone('UTC'))
            elif dt_now.tzinfo is None and due_date.tzinfo:
                dt_now = dt_now.replace(tzinfo=timezone('UTC'))
            return dt_now > due_date

        overdue = filter(lambda score: dictionary.has(score[0]) and is_overdue(score[1][1]), scores.items())
        review = {k: v for _, (k, v) in zip(range(max_len), overdue)}
        log.debug("overdue scores count: %s", len(review))
        return review

    @staticmethod
    def make_cards(length: int, to_review: Scores, new_words: Words, dictionary: Dictionary, mode: QuizMode) -> Tuple[Cards, Scores]:
        """ Returns the question/answer cards list for the quiz
        :param length: number of cards to make
        :param to_review: dictionary of words to review, {word: (score, due_date)}
        :param new_words: list of new words
        :param dictionary: Dictionary instance
        :param mode: quiz mode
        :return: list of dicts {word: articles}[]
        """
        if mode == QuizMode.Review:
            review_len = min(length, len(to_review))
            new_words_count = length - review_len
        else:
            # Takes care of the case when one or both lists don't have enough words for 1/2 quiz length
            review_len, new_words_count = equalizer(len(to_review), len(new_words), length)

        cards = []
        review_words = list(to_review.keys())[:review_len]
        shuffle(review_words)
        for word in review_words:
            article = dictionary.articles(word)
            if article:
                cards.append({'word': word, 'articles': article})
            else:
                # TODO: check the presence of the word in the dictionary before equalizing?
                log.error('Error @ make_cards, missing dictionary word %s', word)
        new_words = new_words[:new_words_count]
        for word in new_words:
            cards.append({'word': word, 'articles': dictionary.articles(word)})
        # TODO: store the scores together with cards
        selected_scores = {word: to_review[word] for word in review_words}
        return cards, selected_scores

    def expected(self, answer):
        return self.active and answer in ['der', 'die', 'das']

    # NOTE: Split into 2 parts?
    # TODO: An option of reporting an error
    def verify_and_update_score(self, answer):
        accepted_answers = self.answer.split("/")  # TODO: set in dictionary
        if answer in accepted_answers:
            result = True
            self.correctly += 1
            new_score_num = min(self.score[0] + 1, max(SCHEDULE.keys()))
        else:
            result = False
            new_score_num = max(self.score[0] - 1, min(SCHEDULE.keys()))
        self.score = (new_score_num, self.next_review(new_score_num))
        return result

    @staticmethod
    def next_review(score_num, now=None):
        """
        :param score_num: current score (after the answer check), Integer
        :param now: current datetime, for testing
        :return: next review datetime for this score
        """
        if now is None:
            now = datetime.now(tz=timezone('UTC'))
        next_review_date = now + SCHEDULE[score_num]
        return next_review_date

    def advance(self):
        self.position += 1

    def stop(self):
        self.active = False

    @property
    def pos(self):
        return self.position + 1

    @property
    def has_questions(self):
        return self.position < self.length

    @property
    def question(self):
        try:
            return self.cards[self.position]['word']
        except IndexError:
            log.error('Index error @ quiz.question, cards: %s, position: %d', self.cards, self.position)
            raise

    @property
    def answer(self):
        try:
            return self.cards[self.position]['articles']
        except IndexError:
            log.error('Index error @ quiz.answer, cards: %s, position: %d', self.cards, self.position)
            raise

    @property
    def score(self):
        """ Returns a tuple (Integer score, Datetime due date) """
        return self.scores.get(self.question) or (0, datetime.now(tz=timezone('UTC')))

    @score.setter
    def score(self, new_val):
        self.scores[self.question] = new_val


class QuizSerializer(serializers.Serializer):
    position = serializers.IntegerField(required=False, default=0)
    correctly = serializers.IntegerField(required=False, default=0)
    active = serializers.BooleanField(required=False, default=False)
    cards = serializers.ListField(
        child=serializers.DictField(child=serializers.CharField(allow_null=True)),
        required=False,
        default=list
    )
    scores = serializers.DictField(
        child=serializers.ListField(),
        required=False,
        default=dict
    )

    def to_internal_value(self, data):
        known_fields = {field: data[field] for field in self.fields if field in data}
        res = super().to_internal_value(known_fields)
        if 'scores' in res and isinstance(res['scores'], dict):
            parsed_scores = {}
            for k, v in res['scores'].items():
                if isinstance(v, (list, tuple)) and len(v) == 2:
                    dt = v[1]
                    if isinstance(dt, str):
                        try:
                            dt = datetime.fromisoformat(dt)
                        except ValueError:
                            pass
                    parsed_scores[k] = (int(v[0]), dt)
                else:
                    parsed_scores[k] = v
            res['scores'] = parsed_scores
        return res

    def to_representation(self, instance):
        res = super().to_representation(instance)
        if 'scores' in res and isinstance(res['scores'], dict):
            ser_scores = {}
            for k, v in res['scores'].items():
                if isinstance(v, (list, tuple)) and len(v) == 2:
                    dt = v[1]
                    if isinstance(dt, datetime):
                        dt = dt.isoformat()
                    ser_scores[k] = [v[0], dt]
                else:
                    ser_scores[k] = v
            res['scores'] = ser_scores
        return res

    def create(self, validated_data):
        return Quiz(**validated_data)

    def update(self, instance, validated_data):
        return self.create(validated_data)

    def dump(self, instance):
        return QuizSerializer(instance).data

    def load(self, data, **kwargs):
        serializer = QuizSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return serializer.save()


# Backward compatibility alias
QuizSchema = QuizSerializer

if __name__ == "__main__":
    pass
