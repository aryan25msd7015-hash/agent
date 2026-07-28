from __future__ import annotations

from config.settings import settings
from skills.browser_automation import bootstrap_google_login


if __name__ == "__main__":
    result = bootstrap_google_login(settings.drive_playwright_user_data_dir, headless=False)
    print(result)
