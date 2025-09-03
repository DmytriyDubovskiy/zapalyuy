import os
from zoneinfo import ZoneInfo
from datetime import timedelta

API_TOKEN = os.getenv("API_TOKEN", "7973792808:AAHstr2BsHAxVIsCfMXhEy9BSdZbkR_6YtQ")
OWNER_ID = 6346589919
KYIV_TZ = ZoneInfo("Europe/Kyiv")
WORKING_DAYS = {0, 1, 2, 3, 4, 5}
START_HOUR = 10
END_HOUR = 20
SESSION_DURATION_MIN = 60
CHECK_EVERY_SEC = 30