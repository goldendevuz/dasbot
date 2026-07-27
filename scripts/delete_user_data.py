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

chat_id = 0  # telegram chat_id
db = Database(settings).connect()
ScoreModel = db["scores"]
StatModel = db["stats"]

log.info("Scores records count: %s", ScoreModel.objects.filter(chat_id=chat_id).count())
# ScoreModel.objects.filter(chat_id=chat_id).delete()

log.info("Stats records count: %s", StatModel.objects.filter(chat_id=chat_id).count())
# StatModel.objects.filter(chat_id=chat_id).delete()
