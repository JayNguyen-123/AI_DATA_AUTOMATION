from playwright.sync_api import sync_playwright
#from app.config import settings

def scrape_with_bright_data(url: str) -> str:
  """
  Scrape dynamic web targets using Bright Data residential proxy networks.
  Clean structural boilerplates to isolate clear text.
  """

  proxy_config = {
      "server": "http://superproxy.io",
      "username": settings.BRIGHT_DATA_ZONE_PROXY.split("@")[0].split("//")[1].split(":")[0],
      "password": settings.BRIGHT_DATA_ZONE_PROXY.split("@")[0].split("//")[1].split(":")[1]
  }

  with sync_playwright() as p:
    # Launching Chromium with explicit proxy configuration parameters
    browser = p.chromium.launch(headless=True, proxy=proxy_config)
    context = browser.new_context(ignore_https_errors=True)
    page = context.new_page()

    try:
      # Enforce 45 seconds navigation deadline
      page.goto(url, wait_until="domcontentloaded", timeout=45000)

      # Drop tracking codes, scripts, and visual tags to reduce context size
      page.locator("script, style, iframe, nav, footer, header").evaluate_all(
          "elements => elements.forEach(el => el.remove())"
      )

      visible_text = page.locator("body").inner_text()
      return visible_text.strip()

    except Exception as e:
      raise RuntimeError(f"Bright Data scraping interaction failed: {str(e)}")
    finally:
      browser.close()
