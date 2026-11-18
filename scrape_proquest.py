import asyncio
import os
import base64
from PIL import Image
from playwright.async_api import async_playwright

async def main():
    print("Starting ProQuest PDF Scraper...")
    
    os.makedirs("temp_pages", exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        print("Navigating to ProQuest Ebook Central...")
        await page.goto("https://ebookcentral.proquest.com/lib/une/reader.action?c=UERG&docID=6727635")
        
        print("\n*** ACTION REQUIRED ***")
        print("1. Please log in using your University credentials.")
        print("2. Navigate to the FIRST page of the book you want to scrape.")
        print("3. Press ENTER in this console when you are ready to begin.")
        input()

        print("Starting PDF extraction...")
        
        image_paths = []
        seen_srcs = set()
        page_num = 1
        
        while True:
            print(f"Capturing page {page_num}...")
            
            current_img = None
            current_src = None
            
            for _ in range(150):  # Wait up to 15 seconds
                all_imgs = await page.locator(".mainViewerImg").element_handles()
                
                for img in all_imgs:
                    in_viewport = await page.evaluate(
                        "(element) => {"
                        "   if (!element) return false;"
                        "   const rect = element.getBoundingClientRect();"
                        "   return rect.top < window.innerHeight && rect.bottom > 0 && rect.width > 0;"
                        "}", img
                    )
                    
                    if not in_viewport:
                        continue
                        
                    src = await img.get_attribute("src")
                    if not src or src in seen_srcs:
                        continue
                        
                    is_loaded = await page.evaluate(
                        "(element) => element.complete && element.naturalHeight !== 0",
                        img
                    )
                    
                    if is_loaded:
                        current_img = img
                        current_src = src
                        break
                
                if current_img:
                    break
                    
                await page.wait_for_timeout(100)
            
            if not current_img:
                print(f"Could not find a new, loaded page image. Did we reach the end of the book?")
                break
                
            try:
                img_path = f"temp_pages/page_{page_num:04d}.png"
                
                # ProQuest uses a clever DRM trick: they send a lower-quality background image,
                # and then use hidden <canvas> elements layered on top of it to draw the crisp, high-res text!
                # We inject JavaScript to create our own canvas, draw the background image, 
                # and then sandwich all the high-res text canvases on top of it.
                b64_data = await page.evaluate(
                    "(img) => {"
                    "    const parent = img.parentElement;"
                    "    const cw = parseInt(img.getAttribute('width')) || img.naturalWidth;"
                    "    const ch = parseInt(img.getAttribute('height')) || img.naturalHeight;"
                    "    const targetWidth = Math.max(cw, img.naturalWidth);"
                    "    const targetHeight = Math.max(ch, img.naturalHeight);"
                    "    "
                    "    const combinedCanvas = document.createElement('canvas');"
                    "    combinedCanvas.width = targetWidth;"
                    "    combinedCanvas.height = targetHeight;"
                    "    const ctx = combinedCanvas.getContext('2d');"
                    "    "
                    "    ctx.fillStyle = 'white';"
                    "    ctx.fillRect(0, 0, targetWidth, targetHeight);"
                    "    ctx.drawImage(img, 0, 0, targetWidth, targetHeight);"
                    "    "
                    "    const canvases = parent.querySelectorAll('canvas');"
                    "    canvases.forEach(c => {"
                    "        ctx.drawImage(c, 0, 0, targetWidth, targetHeight);"
                    "    });"
                    "    "
                    "    return combinedCanvas.toDataURL('image/png').split(',')[1];"
                    "}", current_img
                )
                
                with open(img_path, "wb") as f:
                    f.write(base64.b64decode(b64_data))
                    
                image_paths.append(img_path)
                seen_srcs.add(current_src)
                
            except Exception as e:
                print(f"Error capturing image on page {page_num}: {e}")
                break
            
            # Click the 'Next' button
            try:
                next_button = page.locator("a[title*='Next'], button[title*='Next'], a[aria-label*='Next']").first
                
                if await next_button.is_visible():
                    await next_button.click()
                    page_num += 1
                else:
                    print("Could not find the 'Next' button. Reached the end?")
                    break
            except Exception as e:
                print("Finished or reached the end of the book.")
                break
                
        await browser.close()
        
        # Compile all the images into a PDF
        if image_paths:
            print(f"\nCompiling {len(image_paths)} pages into a PDF...")
            images = [Image.open(img).convert("RGB") for img in image_paths]
            
            pdf_path = "Scraped_Book.pdf"
            if images:
                images[0].save(
                    pdf_path, 
                    save_all=True, 
                    append_images=images[1:]
                )
            print(f"Success! PDF saved as '{pdf_path}'")
        else:
            print("No pages were captured.")

if __name__ == "__main__":
    asyncio.run(main())
