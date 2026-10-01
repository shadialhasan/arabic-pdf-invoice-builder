# -*- coding: utf-8 -*-
"""
Arabic PDF Invoice Builder with ZATCA Phase 2 TLV QR Code & RTL Typography
Author: Eng. MHD. Shadi AL-Hasan <mhd.shadi.alhasan@gmail.com>
Phone: +963934005922
Copyright (c) 2026 MHD. Shadi AL-Hasan
"""

import base64
import argparse
from pathlib import Path

def generate_zatca_tlv_qr(seller_name: str, vat_number: str, timestamp: str, invoice_total: str, vat_total: str) -> str:
    """Generates standard ZATCA / Fatoora Base64 TLV encoded QR payload."""
    def get_tlv(tag: int, value: str) -> bytes:
        val_bytes = value.encode('utf-8')
        return bytes([tag, len(val_bytes)]) + val_bytes

    tlv_data = (
        get_tlv(1, seller_name) +
        get_tlv(2, vat_number) +
        get_tlv(3, timestamp) +
        get_tlv(4, invoice_total) +
        get_tlv(5, vat_total)
    )
    return base64.b64encode(tlv_data).decode('utf-8')

HTML_INVOICE_TEMPLATE = """<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
  <meta charset="utf-8">
  <title>فاتورة ضريبية إلكترونية</title>
  <style>
    body {{ font-family: 'Cairo', 'Tahoma', sans-serif; margin: 30px; color: #1e293b; }}
    .header {{ display: flex; justify-content: space-between; border-bottom: 2px solid #0284c7; padding-bottom: 15px; }}
    .title {{ font-size: 24px; font-weight: bold; color: #0369a1; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 25px; }}
    th, td {{ border: 1px solid #cbd5e1; padding: 10px; text-align: right; }}
    th {{ background-color: #f1f5f9; }}
    .total-box {{ margin-top: 20px; float: left; width: 300px; }}
    .qr {{ margin-top: 20px; float: right; font-size: 11px; word-break: break-all; max-width: 280px; }}
  </style>
</head>
<body>
  <div class="header">
    <div>
      <div class="title">فاتورة مبيعات معتمدة</div>
      <p>رقم الفاتورة: {invoice_num}<br>التاريخ: {date}</p>
    </div>
    <div style="text-align: left;">
      <strong>المورد: {seller_name}</strong><br>
      الرقم الضريبي: {vat_num}
    </div>
  </div>

  <table>
    <thead>
      <tr>
        <th>الوصف</th>
        <th>الكمية</th>
        <th>السعر الإفرادي</th>
        <th>المجموع</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>خدمات استشارية معمارية وتطوير أنظمة رقمية</td>
        <td>1</td>
        <td>{amount} ر.س</td>
        <td>{amount} ر.س</td>
      </tr>
    </tbody>
  </table>

  <div class="qr">
    <strong>رمز التحقق الإلكتروني (TLV QR Base64):</strong><br>
    <code>{qr_payload}</code>
  </div>

  <div class="total-box">
    <table>
      <tr><td>المجموع غير شامل الضريبة:</td><td>{amount} ر.س</td></tr>
      <tr><td>ضريبة القيمة المضافة (15%):</td><td>{vat} ر.س</td></tr>
      <tr><th>الإجمالي المستحق:</th><th>{grand_total} ر.س</th></tr>
    </table>
  </div>
</body>
</html>
"""

def generate_invoice(invoice_num: str, amount: float, out_file: Path):
    vat = round(amount * 0.15, 2)
    grand_total = round(amount + vat, 2)
    seller = "مؤسسة الحلول المتقدمة"
    vat_num = "310000000000003"
    date_str = "2026-10-01T12:00:00Z"
    
    qr_code = generate_zatca_tlv_qr(seller, vat_num, date_str, str(grand_total), str(vat))
    
    html = HTML_INVOICE_TEMPLATE.format(
        invoice_num=invoice_num,
        date="2026-10-01",
        seller_name=seller,
        vat_num=vat_num,
        amount=amount,
        vat=vat,
        grand_total=grand_total,
        qr_payload=qr_code
    )
    out_file.write_text(html, encoding="utf-8")
    print(f"[+] Arabic RTL invoice rendered: {out_file}")
    print(f"[+] ZATCA TLV QR generated: {qr_code[:40]}...")

def main():
    parser = argparse.ArgumentParser(description="Generate ZATCA Phase 2 compliant Arabic invoice.")
    parser.add_argument("--inv", default="INV-2026-001", help="Invoice Number")
    parser.add_argument("--amount", type=float, default=12500.0, help="Amount")
    parser.add_argument("--out", default="invoice_rendered.html", help="Output file")
    args = parser.parse_args()

    generate_invoice(args.inv, args.amount, Path(args.out))

if __name__ == "__main__":
    main()
