import asyncio
from playwright.async_api import async_playwright
import json

BASE_URL = "https://www.withsandra.dev"
ARCHIVE_TEMPLATE = "https://www.withsandra.dev/archive?page={}"

async def get_post_links(page, max_pages=10):
    post_links = set()
    for i in range(max_pages):
        url = ARCHIVE_TEMPLATE.format(i)
        print(f"Checking archive page: {url}")
        await page.goto(url)
        await page.wait_for_timeout(3000)

        anchors = await page.locator('a[href^="/p/"]').all()
        for a in anchors:
            href = await a.get_attribute("href")
            if href:
                full = BASE_URL + href
                post_links.add(full)

        # Stop early if no links are found
        if len(anchors) == 0:
            break

    return list(post_links)

async def scrape_blog_content(page, url):
    await page.goto(url)
    await page.wait_for_timeout(5000)  # Give React time to render

    try:
        # Target <main> first
        main = page.locator("main.flex-grow")

        # Grab first h1 inside it
        title = await main.locator("h1").first.text_content()

        # Grab all paragraph tags inside main
        paragraphs = await main.locator("p").all_text_contents()
        content = "\n\n".join(paragraphs).strip()

        if title and content:
            return {
                "url": url,
                "title": title.strip(),
                "content": content
            }

    except Exception as e:
        print(f"❌ Failed to scrape {url}: {e}")

    return None


async def main():
    all_data = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        post_links = await get_post_links(page, max_pages=10)
        print(f"✅ Found {len(post_links)} posts.")

        for i, link in enumerate(post_links):
            print(f"[{i+1}/{len(post_links)}] Scraping {link}")
            data = await scrape_blog_content(page, link)
            if data:
                all_data.append(data)

        await browser.close()

    with open("withsandra_blogs.json", "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)
    print(f"🎉 Done! Saved {len(all_data)} blog posts to withsandra_blogs.json")

# For notebooks:
await main()

# For .py scripts:
# asyncio.run(main())
