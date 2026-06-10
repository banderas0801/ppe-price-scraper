"""
PPE Price Scraper for VSIP 2023 list
Runs on GitHub Actions (external IP, not blocked by Anthropic proxy)
Saves results to data/prices.json
"""

import requests
import json
import re
import time
import random
from datetime import datetime
from urllib.parse import quote, urlparse

# ── Product list with search terms ────────────────────────────────────────────
PRODUCTS = [
    # Hàng THƯỜNG — tìm Shopee
    {"id": "mu_vai_an_ninh_thuong",      "name": "Mũ vải an ninh thường (lưỡi trai xanh navy bảo vệ)", "sl": 41,  "keywords": ["mũ lưỡi trai xanh navy bảo vệ an ninh", "mũ vải bảo vệ xanh navy"], "source": "shopee"},
    {"id": "mu_vai_chong_nang",           "name": "Mũ vải chống nắng Minh Anh ghi xám",                 "sl": 202, "keywords": ["mũ vải chống nắng ghi xám nam nữ", "nón vải che nắng xám"], "source": "shopee"},
    {"id": "tang_kính_chup_mat",          "name": "Tấm kính chụp mặt chống văng bắn Polycarbonate",     "sl": 96,  "keywords": ["tấm kính chụp mặt bảo hộ polycarbonate chống văng bắn"], "source": "shopee"},
    {"id": "gang_vai_cong_nhan",          "name": "Găng tay vải công nhân",                              "sl": 1908,"keywords": ["găng tay vải công nhân lao động", "găng tay sợi lao động"], "source": "shopee"},
    {"id": "gang_cao_su_dai_tay",         "name": "Găng tay cao su dài tay (ngang khuỷu, Malaysia)",    "sl": 1152,"keywords": ["găng tay cao su dài tay bảo hộ Malaysia", "găng cao su 40cm dài"], "source": "shopee"},
    {"id": "gang_hoa_chat_dai_tay",       "name": "Găng tay hóa chất dài tay (35cm+55cm)",              "sl": 18,  "keywords": ["găng tay chống hóa chất 55cm dài tay", "găng hóa chất 35cm"], "source": "shopee"},
    {"id": "gang_y_te_cimax",             "name": "Găng tay y tế Cimax Malaysia 100c/hộp",              "sl": 10,  "keywords": ["găng tay y tế cimax malaysia", "găng latex cimax 100 cái"], "source": "shopee"},
    {"id": "giay_vai_asia",               "name": "Giày vải Asia xanh tím than lười",                   "sl": 71,  "keywords": ["giày vải Asia xanh tím than lười", "giày ba ta vải xanh đen"], "source": "shopee"},
    {"id": "ung_nhua_trang",              "name": "Ủng nhựa trắng Thùy Dương",                          "sl": 203, "keywords": ["ủng nhựa trắng thùy dương bảo hộ", "ủng cao su trắng vàng lao động"], "source": "shopee"},
    {"id": "giay_batta_pccc",             "name": "Giày batta PCCC trắng sọc đỏ (huấn luyện)",          "sl": 32,  "keywords": ["giày bata trắng sọc đỏ thể thao huấn luyện", "giày vải ba ta trắng đỏ"], "source": "shopee"},
    {"id": "giay_an_ninh_thuong",         "name": "Giày an ninh thường (Oxford da đen buộc dây)",        "sl": 111, "keywords": ["giày oxford da đen đồng phục bảo vệ an ninh", "giày da đen buộc dây đồng phục"], "source": "shopee"},
    {"id": "giay_an_ninh_cd",             "name": "Giày an ninh chuyên dụng (combat boot cao cổ đen)",  "sl": 17,  "keywords": ["giày boot chiến thuật cao cổ đen an ninh", "giày cao cổ đen đồng phục bảo vệ"], "source": "shopee"},
    {"id": "ao_phan_quang_an_ninh",       "name": "Áo phản quang an ninh vàng gile lưới",               "sl": 61,  "keywords": ["áo gile phản quang vàng bảo vệ an ninh", "gile lưới phản quang vàng"], "source": "shopee"},
    {"id": "ao_phan_quang_ve_sinh",       "name": "Áo phản quang vệ sinh lưới thoáng khí",              "sl": 38,  "keywords": ["áo lưới phản quang vệ sinh môi trường", "gile lưới xanh vàng phản quang"], "source": "shopee"},
    {"id": "ao_phan_quang_giam_sat",      "name": "Áo phản quang giám sát an toàn gile đỏ nhiều túi",   "sl": 4,   "keywords": ["gile đỏ nhiều túi hộp kỹ sư giám sát", "áo gile kỹ sư đỏ túi hộp"], "source": "shopee"},
    {"id": "ao_mua_k5_an_ninh",           "name": "Áo mưa bộ K5 an ninh đen xanh đậm",                 "sl": 60,  "keywords": ["bộ áo mưa đen an ninh bảo vệ", "áo mưa bộ đen xanh đồng phục"], "source": "shopee"},
    {"id": "ao_mua_bo_doi",               "name": "Áo mưa bộ quân nhu (công nhân giám sát)",            "sl": 110, "keywords": ["áo mưa bộ đội quân nhu kaki", "áo mưa bộ lính màu kaki"], "source": "shopee"},
    {"id": "qa_cong_nhan",                "name": "QA bảo hộ công nhân 2 màu kem+xanh ngọc + in logo",  "sl": 211, "keywords": ["quần áo bảo hộ kaki 65/35 công nhân nhà máy", "bộ đồng phục công nhân kaki xanh"], "source": "shopee"},
    {"id": "qa_pccc",                     "name": "QA PCCC đỏ Pangrim 65/35 + phản quang",              "sl": 31,  "keywords": ["quần áo PCCC đỏ phản quang bảo hộ", "bộ đồng phục đỏ cứu hỏa pangrim"], "source": "shopee"},
    {"id": "qa_an_ninh_thuong",           "name": "QA an ninh thường xanh nhạt thêu Security",          "sl": 94,  "keywords": ["đồng phục bảo vệ xanh nhạt thêu security", "quần áo bảo vệ xanh nhạt kaki"], "source": "shopee"},
    {"id": "qa_an_ninh_cd",               "name": "QA an ninh chuyên dụng đen thêu Security",           "sl": 34,  "keywords": ["đồng phục bảo vệ đen thêu security", "quần áo bảo vệ đen pangrim"], "source": "shopee"},
    {"id": "ao_khoac_dong_an_ninh",       "name": "Áo khoác mùa đông an ninh xanh cobalt+đen VSIP",     "sl": 58,  "keywords": ["áo khoác đông bảo vệ security xanh đen", "áo jacket bảo vệ mùa đông xanh"], "source": "shopee"},
    {"id": "tap_de_cat_co",               "name": "Tạp dề cắt cỏ chuyên dụng Myung Sung Hàn Quốc",      "sl": 8,   "keywords": ["tạp dề bạt cắt cỏ chuyên dụng hàn quốc", "yếm tạp dề chống bắn đá cắt cỏ"], "source": "shopee"},
    {"id": "qa_chong_hoa_chat",           "name": "QA chống hóa chất Alphatec/Ansell Microgard 2000",   "sl": 18,  "keywords": ["quần áo chống hóa chất alphatec microgard", "bộ liền thân chống hóa chất trắng"], "source": "shopee"},

    # Hàng HỢP QUY — tìm website chuyên ngành
    {"id": "mu_sseda_mat_vuong_trang",    "name": "Mũ SSEDA mặt vuông trắng (Giám sát) HỢP QUY",        "sl": 21,  "keywords": ["mũ bảo hộ sseda mặt vuông trắng"], "source": "baoho_site", "note": "HỢP QUY TT01/2021"},
    {"id": "mu_sseda_mat_tron_vang",      "name": "Mũ SSEDA mặt tròn vàng (Công nhân) HỢP QUY",         "sl": 46,  "keywords": ["mũ bảo hộ sseda mặt tròn vàng"], "source": "baoho_site", "note": "HỢP QUY TT01/2021"},
    {"id": "gang_chong_cat_3m_c5",        "name": "Găng tay chống cắt 3M Cấp 5 HỢP QUY",                "sl": 70,  "keywords": ["găng tay chống cắt 3m cấp độ 5 EN388"], "source": "baoho_site", "note": "HỢP QUY TT01/2021"},
    {"id": "giay_safety_jogger_x11",      "name": "Giày bảo hộ Safety Jogger X11 đen HỢP QUY",          "sl": 30,  "keywords": ["giày safety jogger x11 đen"], "source": "baoho_site", "note": "HỢP QUY TT01/2021"},
    {"id": "day_dai_an_toan",             "name": "Dây đai an toàn toàn thân 2 móc chống sốc HỢP QUY",  "sl": 10,  "keywords": ["dây đai an toàn toàn thân 2 móc chống sốc"], "source": "baoho_site", "note": "HỢP QUY TT01/2021"},
]

# ── HTTP helpers ────────────────────────────────────────────────────────────
UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]

def get_headers(referer="https://shopee.vn/"):
    return {
        "User-Agent": random.choice(UA_LIST),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
        "Referer": referer,
        "Origin": referer.rstrip("/"),
    }

def safe_get(url, **kwargs):
    try:
        r = requests.get(url, timeout=15, **kwargs)
        return r
    except Exception as e:
        print(f"  [ERROR] {e}")
        return None

# ── Shopee scraper ───────────────────────────────────────────────────────────
def init_shopee_session():
    """Init Shopee session to get cookies before searching"""
    session = requests.Session()
    try:
        # Hit homepage first to get session cookies
        r = session.get(
            "https://shopee.vn",
            headers=get_headers(),
            timeout=10,
            allow_redirects=True,
        )
        print(f"  [SESSION] status={r.status_code} cookies={list(session.cookies.keys())}")
        time.sleep(random.uniform(1.0, 2.0))
    except Exception as e:
        print(f"  [SESSION ERROR] {e}")
    return session

# Global session
_session = None

def get_session():
    global _session
    if _session is None:
        _session = init_shopee_session()
    return _session

def shopee_search(keyword, limit=10):
    """Search Shopee VN, sort by sales, return top results"""
    url = (
        f"https://shopee.vn/api/v4/search/search_items"
        f"?by=sales&keyword={quote(keyword)}&limit={limit}"
        f"&newest=0&order=desc&page_type=search&scenario=PAGE_OTHERS&version=2"
    )
    session = get_session()
    headers = {
        **get_headers("https://shopee.vn/search"),
        "X-Api-Source": "pc",
        "X-Shopee-Language": "vi",
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    }
    try:
        r = session.get(url, headers=headers, timeout=15)
    except Exception as e:
        print(f"  [SHOPEE SEARCH ERROR] {e}")
        return []

    if not r or r.status_code != 200:
        print(f"  [SHOPEE SEARCH] status={getattr(r,'status_code','err')} kw={keyword[:40]}")
        # Try fallback: Tiki only for this product
        return []
    try:
        data = r.json()
        items = data.get("items", []) or []
        results = []
        for item in items:
            item_basic = item.get("item_basic") or item
            price_raw = item_basic.get("price") or item_basic.get("price_min") or 0
            price = price_raw / 100000 if price_raw else 0
            sold = item_basic.get("historical_sold") or item_basic.get("sold") or 0
            rating = (item_basic.get("item_rating") or {}).get("rating_star") or 0
            results.append({
                "name": item_basic.get("name", ""),
                "price": round(price),
                "sold": sold,
                "rating": round(rating, 1),
                "shop_id": item_basic.get("shopid"),
                "item_id": item_basic.get("itemid"),
                "url": f"https://shopee.vn/product/{item_basic.get('shopid')}/{item_basic.get('itemid')}",
                "is_mall": item_basic.get("is_official_shop", False),
                "platform": "shopee",
            })
        print(f"  [SHOPEE] Got {len(results)} results for: {keyword[:40]}")
        return results
    except Exception as e:
        print(f"  [PARSE ERROR] {e}")
        return []

def shopee_get_item(shop_id, item_id):
    """Get specific item detail by IDs"""
    url = f"https://shopee.vn/api/v2/item/get?itemid={item_id}&shopid={shop_id}"
    r = safe_get(url, headers=get_headers())
    if not r or r.status_code != 200:
        return None
    try:
        data = r.json()
        item = (data.get("data") or data.get("item") or {})
        price_raw = item.get("price") or item.get("price_min") or 0
        return {
            "name": item.get("name",""),
            "price": round(price_raw / 100000) if price_raw else 0,
            "sold": item.get("historical_sold") or item.get("sold") or 0,
            "rating": (item.get("item_rating") or {}).get("rating_star") or 0,
            "in_stock": item.get("stock", 0) > 0,
            "url": f"https://shopee.vn/product/{shop_id}/{item_id}",
        }
    except Exception as e:
        print(f"  [ITEM GET ERROR] {e}")
        return None

def pick_best_shopee_result(results, expected_price=None):
    """Pick best result: mall > rating > sold, filter obvious mismatches"""
    if not results:
        return None
    # Filter out items with 0 price
    results = [r for r in results if r.get("price", 0) > 0]
    if not results:
        return None
    # Sort: mall first, then rating desc, then sold desc
    results.sort(key=lambda x: (
        not x.get("is_mall", False),
        -(x.get("rating") or 0),
        -(x.get("sold") or 0)
    ))
    return results[0]

# ── Tiki scraper ─────────────────────────────────────────────────────────────
def tiki_search(keyword, limit=5):
    """Search Tiki VN"""
    url = f"https://tiki.vn/api/v2/products?q={quote(keyword)}&limit={limit}&sort=top_seller"
    r = safe_get(url, headers=get_headers("https://tiki.vn/"))
    if not r or r.status_code != 200:
        return []
    try:
        data = r.json()
        items = data.get("data", []) or []
        results = []
        for item in items:
            results.append({
                "name": item.get("name", ""),
                "price": item.get("price", 0),
                "sold": item.get("quantity_sold", {}).get("value", 0) if isinstance(item.get("quantity_sold"), dict) else 0,
                "rating": item.get("rating_average", 0),
                "url": f"https://tiki.vn/{item.get('url_path', '')}",
                "is_mall": item.get("is_official", False),
                "is_official": item.get("is_official", False),
                "platform": "tiki",
            })
        return results
    except Exception as e:
        print(f"  [TIKI PARSE ERROR] {e}")
        return []

# ── Baoho site scraper ───────────────────────────────────────────────────────
BAOHO_SITES = {
    "mu_sseda_mat_vuong_trang": {
        "url": "https://namtrungsafety.com/mu-bao-ho-sseda-mat-vuong.html",
        "price_hint": 150000,
        "note": "150k (miền Nam +20k ship) — namtrungsafety.com hotline: 0933 911 900"
    },
    "mu_sseda_mat_tron_vang": {
        "url": "https://namtrungsafety.com/mu-bao-ho-sseda-mat-tron.html",
        "price_hint": 140000,
        "note": "140k — namtrungsafety.com hotline: 0933 911 900"
    },
    "gang_chong_cat_3m_c5": {
        "url": "https://baohobinhan.com/products/gang-tay-chong-cat-3m-cap-do-5",
        "price_hint": 80000,
        "note": "~80k/đôi — thienbang.com hotline: 0909 702 727"
    },
    "giay_safety_jogger_x11": {
        "url": "https://safetyjoggervietnam.com/giay-bao-ho-safety-jogger-x11",
        "price_hint": 900000,
        "note": "~850-950k — safetyjoggervietnam.com hotline: 0877 904 787"
    },
    "day_dai_an_toan": {
        "url": "https://xuyenadaithanh.com/day-dai-an-toan-toan-than",
        "price_hint": 350000,
        "note": "~300-400k — xuyenadaithanh.com / baohoxanh.com"
    },
}

def get_baoho_site_price(product_id):
    """Use known price hints for PPE specialist sites (can't scrape dynamically)"""
    site_data = BAOHO_SITES.get(product_id)
    if not site_data:
        return None
    r = safe_get(site_data["url"], headers=get_headers(site_data["url"]))
    if r and r.status_code == 200:
        # Try to extract price from HTML
        text = r.text
        # Look for price patterns in VND
        patterns = [
            r'(\d{1,3}(?:\.\d{3})+)(?:\s*₫|VND|đ)',
            r'"price":\s*"?(\d+)"?',
            r'price["\s:]+(\d{5,7})',
            r'(\d{3,4}\.000)',
        ]
        for pat in patterns:
            matches = re.findall(pat, text)
            for m in matches:
                clean = m.replace(".", "").replace(",", "")
                try:
                    price = int(clean)
                    if 50000 < price < 5000000:
                        return {
                            "price": price,
                            "source": site_data["url"],
                            "note": site_data["note"],
                            "scraped": True,
                        }
                except:
                    continue
    # Fallback to price hint
    return {
        "price": site_data["price_hint"],
        "source": site_data["url"],
        "note": site_data["note"],
        "scraped": False,
        "hint_only": True,
    }

# ── Main runner ───────────────────────────────────────────────────────────────
def run_all():
    results = {}
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    for prod in PRODUCTS:
        pid = prod["id"]
        print(f"\n[{pid}] {prod['name'][:50]}")
        
        entry = {
            "id": pid,
            "name": prod["name"],
            "sl": prod["sl"],
            "source_type": prod["source"],
            "note": prod.get("note", ""),
            "scraped_at": timestamp,
            "results": [],
            "best": None,
        }
        
        if prod["source"] == "shopee":
            # Try each keyword, collect results
            all_results = []
            for kw in prod["keywords"][:2]:  # max 2 keywords to avoid rate limit
                print(f"  Search: {kw[:50]}")
                items = shopee_search(kw, limit=5)
                all_results.extend(items)
                time.sleep(random.uniform(1.5, 3.0))
            
            # Also try Tiki
            tiki_items = tiki_search(prod["keywords"][0], limit=3)
            for t in tiki_items:
                t["platform"] = "tiki"
            for s in all_results:
                s["platform"] = "shopee"
            
            combined = all_results + tiki_items
            best = pick_best_shopee_result(combined)
            
            entry["results"] = combined[:8]
            entry["best"] = best
            if best:
                print(f"  ✅ Best: {best['name'][:40]} | {best['price']:,}đ | ⭐{best.get('rating',0)} | sold:{best.get('sold',0)}")
            else:
                print(f"  ❌ No results")
        
        elif prod["source"] == "baoho_site":
            site_result = get_baoho_site_price(pid)
            entry["best"] = site_result
            entry["results"] = [site_result] if site_result else []
            if site_result:
                scraped = "scraped" if site_result.get("scraped") else "hint"
                print(f"  ✅ [{scraped}] {site_result['price']:,}đ | {site_result.get('note','')[:60]}")
        
        results[pid] = entry
        time.sleep(random.uniform(1.0, 2.0))
    
    # Summary
    has_price = sum(1 for v in results.values() if v.get("best") and v["best"].get("price"))
    print(f"\n{'='*60}")
    print(f"DONE: {has_price}/{len(results)} products have price")
    
    return {
        "scraped_at": timestamp,
        "total": len(results),
        "has_price": has_price,
        "products": results,
    }

if __name__ == "__main__":
    import sys
    data = run_all()
    output_path = sys.argv[1] if len(sys.argv) > 1 else "data/prices.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\nSaved to {output_path}")
