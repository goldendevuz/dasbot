import logging
import sys

import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dasbot.db.database import Database
from dasbot.config import settings

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%m.%d %H:%M:%S",
)
log = logging.getLogger(__name__)

db = Database(settings).connect()
ScoreModel = db["scores"]

query = {"word": "Pro"}
log.info("Scores records: %s", ScoreModel.objects.filter(**query).count())
# ScoreModel.objects.filter(**query).delete()
