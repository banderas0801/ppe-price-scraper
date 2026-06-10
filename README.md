# PPE Price Scraper — VSIP 2023

Auto-scrape giá PPE từ Shopee VN, Tiki VN và các website bảo hộ chuyên ngành.  
Chạy qua **GitHub Actions** (IP ngoài, không bị block) → lưu JSON → đọc lại từ bất kỳ đâu.

---

## Cách dùng nhanh

### Bước 1 — Fork repo này về GitHub của bạn

```bash
# Hoặc clone và push lên repo mới
git clone https://github.com/YOUR_USERNAME/ppe-price-scraper
```

### Bước 2 — Chạy scraper lần đầu

Vào **Actions** tab → chọn `Scrape PPE Prices` → **Run workflow**

Chờ ~5 phút. Kết quả lưu tự động vào `data/prices.json`.

### Bước 3 — Đọc giá và điền Excel

```bash
pip install requests openpyxl

python scraper/read_prices.py \
  --github_url https://raw.githubusercontent.com/YOUR_USERNAME/ppe-price-scraper/main/data/prices.json \
  --excel_in   "3__SỐ_LƯỢNG___PHÂN_LOẠI_CHI_TIẾT__1_.xlsx" \
  --excel_out  "BaoGia_PPE_VSIP_2024_Final.xlsx"
```

---

## Cấu trúc

```
ppe-price-scraper/
├── .github/workflows/
│   └── scrape.yml          # GitHub Action — chạy tự động mỗi ngày 7AM
├── scraper/
│   ├── scrape.py           # Core scraper (Shopee API v4 + Tiki + baoho sites)
│   ├── validate.py         # Validate giá + generate summary.json
│   └── read_prices.py      # Đọc JSON từ GitHub → điền Excel
├── data/
│   ├── prices.json         # Raw scraped data (auto-updated)
│   └── summary.json        # Summary + warnings (auto-updated)
└── README.md
```

---

## Shopee API đang dùng

```
# Search by keyword, sort by sales:
GET https://shopee.vn/api/v4/search/search_items
  ?by=sales&keyword={kw}&limit=10&newest=0&order=desc
  &page_type=search&scenario=PAGE_OTHERS&version=2

# Price field: item_basic.price / 100000 = VND

# Get item detail by ID:
GET https://shopee.vn/api/v2/item/get?itemid={id}&shopid={id}
```

Source: phân tích từ [duyetdev/pricetrack](https://github.com/duyetdev/pricetrack)  
và [akherlan/onlineshop](https://github.com/akherlan/onlineshop)

---

## Lịch chạy tự động

- Mỗi ngày 7:00 SA (GMT+7) — `cron: "0 0 * * *"`
- Hoặc chạy thủ công từ Actions tab bất kỳ lúc nào

---

## Giới hạn

| Loại | Giá | Nguồn |
|---|---|---|
| Hàng **THƯỜNG** | Shopee + Tiki (auto) | Real-time |
| Hàng **HỢP QUY** (SSEDA, 3M, Safety Jogger...) | Price hint (cần verify) | Website chuyên ngành |
| Hàng HQ chưa tìm được | `null` | Cần liên hệ trực tiếp |

> Hàng hợp quy TT01/2021 → BẮT BUỘC liên hệ đại lý chính hãng để có giấy CN.  
> Không mua Shopee random dù giá rẻ hơn.
