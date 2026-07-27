import os
import aiounittest
from unittest.mock import AsyncMock, ANY

os.environ["ENV_FOR_DYNACONF"] = "test"
from dasbot.config import settings
from dasbot.db.database import Database
Database(settings).connect()

from aiogram.types import InlineKeyboardMarkup
from dasbot.models.db_models import ChatModel, ScoreModel, StatModel
from dasbot.db.chats_repo import ChatsRepo
from dasbot.db.stats_repo import StatsRepo
from dasbot.settings_controller import SettingsController


class TestSettingsController(aiounittest.AsyncTestCase):
    def setUp(self):
        Database(settings).connect()
        ChatModel.objects.all().delete()
        ScoreModel.objects.all().delete()
        StatModel.objects.all().delete()
        chats_repo = ChatsRepo(ChatModel, ScoreModel)
        stats_repo = StatsRepo(ScoreModel, StatModel, "test_dictionary")
        self.menucon = SettingsController(chats_repo, stats_repo)

    async def test_main(self):
        message_mock = AsyncMock()
        await self.menucon.main(message=message_mock)
        message_mock.answer.assert_called_with(text="Please select an option", reply_markup=ANY)

    def test_settings_kb(self):
        level = 1
        menu_id = "quiz_time"
        keyboard = self.menucon.settings_kb(level, menu_id)
        self.assertIsInstance(keyboard, InlineKeyboardMarkup)
        self.assertEqual(len(keyboard.inline_keyboard), 3)
        self.assertEqual(keyboard.inline_keyboard[-1][0].callback_data, "menu:2:quiz_time:off")
