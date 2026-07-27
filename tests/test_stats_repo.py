import os
import unittest

os.environ["ENV_FOR_DYNACONF"] = "test"
from dasbot.config import settings
from dasbot.db.database import Database
Database(settings).connect()

from dasbot.models.db_models import ScoreModel, StatModel, DictionaryModel
from dasbot.db.stats_repo import StatsRepo


class TestStatsRepo(unittest.TestCase):
    def setUp(self):
        Database(settings).connect()
        ScoreModel.objects.all().delete()
        StatModel.objects.all().delete()
        DictionaryModel.objects.all().delete()
        self.stats_repo = StatsRepo(ScoreModel, StatModel, "test_dictionary")

    def test_get_stats_no_data(self):
        stats = self.stats_repo.get_stats(1)
        self.assertDictEqual({"touched": 0, "mistakes_30days": []}, stats)


if __name__ == "__main__":
    unittest.main()
