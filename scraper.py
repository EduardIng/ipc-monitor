"""
Playwright scraper for https://ipc.gov.cz/informace-o-stavu-rizeni/

The page uses Vue.js with custom dropdown components (likely vue-select).
Dropdowns are NOT native <select> — interact by clicking trigger, then
clicking the matching list item by its text content.

If selectors break after site updates, inspect the page with:
    chromium --headless=new --dump-dom https://ipc.gov.cz/informace-o-stavu-rizeni/
or run scraper.py with headless=False to watch the browser.
"""
import asyncio
import logging

from playwright.async_api import async_playwright, TimeoutError as PWTimeout

logger = logging.getLogger(__name__)

URL = "https://ipc.gov.cz/informace-o-stavu-rizeni/"
TIMEOUT = 30_000  # ms


async def _fill_form_and_get_status(page, number: str, typ: str, year: str) -> str:
    await page.goto(URL, timeout=TIMEOUT)

    # --- Reference number ---
    await page.wait_for_selector('input[name="proceedings.referenceNumber"]', timeout=TIMEOUT)
    await page.fill('input[name="proceedings.referenceNumber"]', number)

    # --- Typ řízení dropdown ---
    # Vue-select: the visible trigger is a div with role="combobox" or class "vs__search"
    # Strategy: find the fieldset/div labelled "Typ řízení", click its dropdown trigger
    await _select_dropdown(page, label_text="Typ řízení", option_text=typ)

    # --- Rok dropdown ---
    await _select_dropdown(page, label_text="Rok", option_text=year)

    # --- Submit ---
    await page.click('button:has-text("Ověřit")')

    # --- Wait for result ---
    # The result appears in an .alert element or a div with role="alert"
    result_selector = '.alert, [role="alert"], .result-message, [class*="result"]'
    await page.wait_for_selector(result_selector, timeout=TIMEOUT)

    # Get all matching elements and return the most relevant text
    elements = await page.query_selector_all(result_selector)
    texts = []
    for el in elements:
        t = (await el.inner_text()).strip()
        if t:
            texts.append(t)

    return " | ".join(texts) if texts else ""


async def _select_dropdown(page, label_text: str, option_text: str):
    """
    Open a Vue-select dropdown identified by its nearby label text,
    then click the option matching option_text.
    """
    # Find the dropdown container near the label
    label = page.locator(f'label:has-text("{label_text}")')
    count = await label.count()

    if count > 0:
        # Click the dropdown toggle within the same form group as this label
        parent = label.locator("xpath=..")
        toggle = parent.locator(".vs__dropdown-toggle, [class*='dropdown-toggle'], [class*='select']").first
        await toggle.click()
    else:
        # Fallback: find any clickable element with the label text
        await page.click(f'text="{label_text}"')

    # Wait for options list to appear
    await page.wait_for_selector(
        ".vs__dropdown-menu, [class*='dropdown-menu'], [class*='dropdown-list']",
        timeout=TIMEOUT,
    )

    # Click the option matching the text
    option = page.locator(
        f".vs__dropdown-menu li:has-text('{option_text}'), "
        f"[class*='dropdown-menu'] li:has-text('{option_text}'), "
        f"[class*='dropdown-option']:has-text('{option_text}')"
    ).first
    await option.click()

    # Wait for dropdown to close
    await page.wait_for_selector(
        ".vs__dropdown-menu, [class*='dropdown-menu']",
        state="hidden",
        timeout=TIMEOUT,
    )


async def check_application(number: str, typ: str, year: str) -> str:
    """
    Returns the status text from the page, or raises an exception.
    Called once per application per check run.
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
