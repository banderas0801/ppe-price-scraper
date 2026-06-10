import asyncio, json, sys, random
from datetime import datetime
from playwright.async_api import async_playwright

PRODUCTS = [
    {"id": "gang_vai_cong_nhan", "name": "Gang tay vai cong nhan", "sl": 1908, "kw": "gang tay vai cong nhan lao dong"},
    {"id": "gang_cao_su", "name": "Gang tay cao su dai tay", "sl": 1152, "kw": "gang tay cao su dai tay bao ho"},
    {"id": "ao_phan_quang_an_ninh", "name": "Ao phan quang an ninh vang", "sl": 61, "kw": "ao gile phan quang vang bao ve"},
    {"id": "ao_mua_k5", "name": "Ao mua K5 an ninh", "sl": 60, "kw": "bo ao mua den xanh bao ve"},
    {"id": "qa_cong_nhan", "name": "QA cong nhan kem xanh", "sl": 211, "kw": "quan ao bao ho kaki cong nhan"},
    {"id": "giay_an_ninh_thuong", "name": "Giay an ninh thuong Oxford", "sl": 111, "kw": "giay oxford da den dong phuc bao ve"},
    {"id": "mu_sseda_trang", "name": "Mu SSEDA trang mat vuong", "sl": 21, "kw": "mu bao ho sseda mat vuong trang"},
    {"id": "day_dai_an_toan", "name": "Day dai an toan 2 moc", "sl": 10, "kw": "day dai an toan toan than 2 moc"},
]

async def search_shopee(page, keyword, limit=5):
    results = []
    api_data = []
    async def handle_response(response):
        if "search/search_items" in response.url and response.status == 200:
            try:
                body = await response.json()
                api_data.append(body)
            except:
                pass
    page.on("response", handle_response)
    try:
        await page.goto(f"https://shopee.vn/search?keyword={keyword}&sortBy=sales", wait_until="networkidle", timeout=25000)
        await asyncio.sleep(random.uniform(2, 3))
        for data in api_data:
            for item in (data.get("items") or [])[:limit]:
                ib = item.get("item_basic") or item
                price_raw = ib.get("price") or ib.get("price_min") or 0
                price = round(price_raw / 100000) if price_raw else 0
                if price > 0:
                    results.append({"name": ib.get("name",""), "price": price, "sold": ib.get("historical_sold") or 0, "rating": round((ib.get("item_rating") or {}).get("rating_star") or 0, 1), "url": f"https://shopee.vn/product/{ib.get('shopid')}/{ib.get('itemid')}", "is_mall": bool(ib.get("is_official_shop")), "platform": "shopee"})
            if results:
                break
    except Exception as e:
        print(f"  [ERR] {e}")
    finally:
        page.remove_listener("response", handle_response)
    return results

def pick_best(results):
    results = [r for r in results if r.get("price", 0) > 0]
    if not results:
        return None
    results.sort(key=lambda x: (not x.get("is_mall"), -(x.get("rating") or 0), -(x.get("sold") or 0)))
    return results[0]

async def run():
    output_path = sys.argv[1] if len(sys.argv) > 1 else "data/prices.json"
    timestamp = datetime.utcnow().isoformat() + "Z"
    all_results = {}
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox","--disable-setuid-sandbox","--disable-blink-features=AutomationControlled","--disable-dev-shm-usage"])
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36", viewport={"width": 1280, "height": 800}, locale="vi-VN", timezone_id="Asia/Ho_Chi_Minh")
        await context.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined});")
        page = await context.new_page()
        print("Warming up...")
        try:
            await page.goto("https://shopee.vn", wait_until="networkidle", timeout=25000)
            await asyncio.sleep(random.uniform(2, 3))
            print(f"  OK. Cookies: {len(await context.cookies())}")
        except Exception as e:
            print(f"  Warmup error: {e}")
        for prod in PRODUCTS:
            pid = prod["id"]
            print(f"\n[{pid}] {prod['name'][:45]}")
            results = await search_shopee(page, prod["kw"], limit=5)
            best = pick_best(results)
            all_results[pid] = {"id": pid, "name": prod["name"], "sl": prod["sl"], "scraped_at": timestamp, "results": results[:5], "best": best}
            print(f"  {'✅ ' + str(best['price']) + 'd' if best else '❌ No results'}")
            await asyncio.sleep(random.uniform(2, 4))
        await browser.close()
    has_price = sum(1 for v in all_results.values() if v.get("best") and v["best"].get("price"))
    output = {"scraped_at": timestamp, "total": len(all_results), "has_price": has_price, "products": all_results}
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\nDONE: {has_price}/{len(all_results)} | Saved to {output_path}")

if __name__ == "__main__":
    asyncio.run(run())
