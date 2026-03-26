"""
Playwright scraper for https://ipc.gov.cz/informace-o-stavu-rizeni/

The page uses React Select dropdowns (class "react-select__control").
Dropdowns are NOT native <select> — click the control to open, then
click the matching option by text content.

Cookie consent dialog appears on first load — dismissed automatically.

If selectors break after site updates, run with headless=False to debug:
    change headless=True → headless=False in check_application()
"""
import asyncio
import logging

from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

URL = "https://ipc.gov.cz/informace-o-stavu-rizeni/"
TIMEOUT = 60_000  # ms — increased from 30s; site loads React components slowly


async def _dismiss_cookies(page):
    """Dismiss cookie consent banner if present."""
    try:
        btn = page.locator('button:has-text("ODMÍTNOUT")')
        if await btn.count() > 0:
            await btn.first.click(timeout=5000)
            logger.debug("Cookie consent dismissed")
    except Exception:
        pass  # No cookie dialog or already dismissed


async def _select_react_dropdown(page, nth: int, option_text: str):
    """
    Open the nth react-select dropdown on the page (0-indexed) and select
    the option whose text contains option_text.
    """
    controls = page.locator(".react-select__control")
    await controls.nth(nth).click(timeout=TIMEOUT)
    # Wait for options menu
    await page.wait_for_selector(".react-select__menu", timeout=TIMEOUT)
    # Click the matching option
    option = page.locator(f".react-select__option:has-text('{option_text}')").first
    await option.click(timeout=TIMEOUT)
    # Wait for menu to close
    await page.wait_for_selector(".react-select__menu", state="hidden", timeout=TIMEOUT)


async def _fill_form_and_get_status(page, number: str, typ: str, year: str) -> str:
    await page.goto(URL, timeout=TIMEOUT)
    await page.wait_for_load_state("networkidle", timeout=TIMEOUT)

    await _dismiss_cookies(page)

    # --- Reference number ---
    await page.wait_for_selector('input[name="proceedings.referenceNumber"]', timeout=TIMEOUT)
    await page.fill('input[name="proceedings.referenceNumber"]', number)

    # --- Typ řízení (1st react-select on the form, index 0) ---
    await _select_react_dropdown(page, nth=0, option_text=typ)

    # --- Rok (2nd react-select on the form, index 1) ---
    await _select_react_dropdown(page, nth=1, option_text=year)

    # --- Submit (button text is uppercase on the site) ---
    await page.click('button:has-text("OVĚŘIT")', timeout=TIMEOUT)

    # --- Wait for result ---
    result_selector = '.alert, [role="alert"], [class*="notification"], [class*="result-text"]'
    await page.wait_for_selector(result_selector, timeout=TIMEOUT)

    elements = await page.query_selector_all(result_selector)
    texts = []
    for el in elements:
        t = (await el.inner_text()).strip()
        if t:
            texts.append(t)

    return " | ".join(texts) if texts else ""


async def check_application(number: str, typ: str, year: str) -> str:
    """
    Returns the status text from the page, or raises an exception.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )
        page = await context.new_page()
        try:
            logger.debug(f"Checking {number}/{typ}-{year}")
            status = await _fill_form_and_get_status(page, number, typ, year)
            logger.debug(f"Got status: {status!r}")
            return status
        finally:
            await browser.close()
