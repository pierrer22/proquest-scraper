# ProQuest Ebook Central Scraper

Automates capturing pages from ProQuest Ebook Central in a Playwright Chromium browser and compiling them into a PDF (`Scraped_Book.pdf`).

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install playwright Pillow
playwright install chromium
```

## Usage

1. Update the target URL in `scrape_proquest.py` if needed (line 18).
2. Run the script:
   ```bash
   python scrape_proquest.py
   ```
3. Log in with your institution credentials in the opened browser window, navigate to the first page you want to capture, and zoom in for higher image resolution.
4. Press `Enter` in the terminal to start capturing.

Captured PNG pages are saved in `temp_pages/` and compiled into `Scraped_Book.pdf`.
