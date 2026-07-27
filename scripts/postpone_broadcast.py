# Postpones overdue quizzes by 24 hours
# May need to run several times if broadcast was out for more than a day

import logging
import sys
from datetime import datetime, timedelta, timezone
from django.db.models import F

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
now = datetime.now(tz=timezone.utc)

pending_chats = ChatModel.objects.filter(subscribed=True, quiz_scheduled_time__lte=now)
log.info(f"Pending: {pending_chats.count()}")

updated_count = pending_chats.update(quiz_scheduled_time=F("quiz_scheduled_time") + timedelta(days=1))
log.info(f"Updated {updated_count} records")
