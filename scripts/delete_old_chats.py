# Delete old chats that have not been active for over 3 years

import logging
import sys
from datetime import datetime, timedelta, timezone

import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dasbot.config import settings
from dasbot.db.database import Database

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%m.%d %H:%M:%S",
)
log = logging.getLogger(__name__)

db = Database(settings).connect()
ChatModel = db["chats"]
ScoreModel = db["scores"]
cutoff = datetime.now(tz=timezone.utc) - timedelta(days=365 * 3)

old_chats = ChatModel.objects.filter(last_seen__lte=cutoff)
log.info(f"Active more than 3 years ago: {old_chats.count()}")

for chat in old_chats:
    scores_count = ScoreModel.objects.filter(chat_id=chat.chat_id).count()
    log.info(f"Deleting {chat.chat_id} with {scores_count} score(s), last seen at {chat.last_seen}")
    ScoreModel.objects.filter(chat_id=chat.chat_id).delete()
    chat.delete()
