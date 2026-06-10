"""
Validate scraped prices and generate summary.json
"""
import json, sys, re
from datetime import datetime

def validate_and_summarize(input_path="data/prices.json", output_path="data/summary.json"):
    with open(input_path, encoding="utf-8") as f:
        data = json.load(f)

    products = data.get("products", {})
    summary_rows = []
    warnings = []
    total_cost_min = 0
    total_cost_max = 0

    for pid, prod in products.items():
        best = prod.get("best")
        sl = prod.get("sl", 0)
        name = prod.get("name", pid)
        note = prod.get("note", "")
        is_hoqy = "HỢP QUY" in note

        row = {
            "id": pid,
            "name": name,
            "sl": sl,
            "is_hop_quy": is_hoqy,
            "note": note,
        }

        if best and best.get("price"):
            price = best["price"]
            thanh_tien = price * sl

            # Sanity checks
            if price < 5000:
                warnings.append(f"⚠️ {name}: giá quá thấp ({price:,}đ) — có thể lỗi parse")
            elif price > 10_000_000:
                warnings.append(f"⚠️ {name}: giá quá cao ({price:,}đ) — kiểm tra lại")

            row.update({
                "don_gia": price,
                "thanh_tien": thanh_tien,
                "url": best.get("url", ""),
                "platform": best.get("platform", best.get("source", "")),
                "rating": best.get("rating", ""),
                "sold": best.get("sold", ""),
                "is_mall": best.get("is_mall", False),
                "hint_only": best.get("hint_only", False),
                "status": "✅ Có giá",
            })
            total_cost_min += thanh_tien
            total_cost_max += thanh_tien
        else:
            row.update({
                "don_gia": None,
                "thanh_tien": None,
                "url": "",
                "status": "❌ Chưa có giá" if not is_hoqy else "📞 HỢP QUY — cần liên hệ trực tiếp",
            })
            warnings.append(f"Missing price: {name}")

        summary_rows.append(row)

    has_price = sum(1 for r in summary_rows if r["don_gia"])
    total = len(summary_rows)

    summary = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "source_file": input_path,
        "stats": {
            "total_products": total,
            "has_price": has_price,
            "missing_price": total - has_price,
            "completion_pct": round(has_price / total * 100, 1),
            "est_total_cost_vnd": total_cost_min,
        },
        "warnings": warnings,
        "products": summary_rows,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    # Print report
    print(f"\n{'='*60}")
    print(f"SUMMARY: {has_price}/{total} products ({summary['stats']['completion_pct']}%)")
    print(f"Est. total cost: {total_cost_min:,.0f} VND")
    print(f"\n{'STT':<3} {'TÊN SP':<45} {'SL':>5} {'ĐƠN GIÁ':>12} {'THÀNH TIỀN':>14} STATUS")
    print("-"*110)
    for i, r in enumerate(summary_rows, 1):
        gia_str = f"{r['don_gia']:>12,}" if r['don_gia'] else f"{'N/A':>12}"
        tt_str  = f"{r['thanh_tien']:>14,}" if r['thanh_tien'] else f"{'N/A':>14}"
        hint = " [hint]" if r.get("hint_only") else ""
        print(f"{i:<3} {r['name'][:45]:<45} {r['sl']:>5} {gia_str} {tt_str} {r['status']}{hint}")

    if warnings:
        print(f"\n⚠️  {len(warnings)} warnings:")
        for w in warnings:
            print(f"  - {w}")

    print(f"\nSaved summary to {output_path}")
    return summary

if __name__ == "__main__":
    input_path = sys.argv[1] if len(sys.argv) > 1 else "data/prices.json"
    validate_and_summarize(input_path)
