from __future__ import annotations

import logging

from playwright.sync_api import sync_playwright

logger = logging.getLogger("mutsniper.auth")

MUT_WEB_APP_URL = "https://www.easports.com/madden-nfl/ultimate-team/web-app/"


def login(session_path: str) -> None:
    """Open a real browser window for the user to complete EA login
    (including 2FA/captcha) by hand, then persist the resulting session
    (cookies + storage) so the scanner can reuse it without logging in
    again each run."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(MUT_WEB_APP_URL)

        print(
            "A browser window has opened. Log into your EA account and open "
            "the auction house so the session is fully initialized.\n"
            "Once you can see live auction listings, come back here and "
            "press Enter."
        )
        input()

        context.storage_state(path=session_path)
        browser.close()

    logger.info("Session saved to %s", session_path)


def load_context(playwright, session_path: str):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(storage_state=session_path)
    return browser, context
