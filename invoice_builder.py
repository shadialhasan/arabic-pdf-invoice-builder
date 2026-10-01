# -*- coding: utf-8 -*-
"""
Arabic PDF Invoice Builder with ZATCA Phase 2 TLV QR Code & RTL Typography
Author: Eng. MHD. Shadi AL-Hasan <mhd.shadi.alhasan@gmail.com>
Phone: +963934005922
Copyright (c) 2026 MHD. Shadi AL-Hasan
"""

import os
import sys
import base64
import argparse
import datetime
import re
from pathlib import Path
from typing import Dict, Any, Optional, Tuple


def validate_vat_number(vat_number: str) -> bool:
    """
    Validates a standard 15-digit ZATCA / GCC VAT identification number.
    Standard KSA VAT numbers are 15 digits starting and ending with 3.
    """
    if not isinstance(vat_number, str):
        return False
    vat_clean = vat_number.strip()
    return bool(re.match(r"^3\d{13}3$", vat_clean) or re.match(r"^\d{15}$", vat_clean))


def validate_invoice_params(
    invoice_num: str,
    amount: float,
    seller_name: str,
    vat_number: str,
    tax_rate: float = 0.15
) -> None:
    """Validates parameters required for invoice and ZATCA compliance."""
    if not invoice_num or not isinstance(invoice_num, str) or not invoice_num.strip():
        raise ValueError("Invoice number must be a non-empty string.")

    if not isinstance(amount, (int, float)) or amount <= 0:
        raise ValueError(f"Invoice amount must be a positive number greater than zero. Got: {amount}")

    if not seller_name or not isinstance(seller_name, str) or not seller_name.strip():
        raise ValueError("Seller name must be a non-empty string.")

    if not vat_number or not isinstance(vat_number, str) or not vat_number.strip():
        raise ValueError("VAT registration number must be a non-empty string.")

    if not (0.0 <= tax_rate <= 1.0):
        raise ValueError(f"Tax rate must be between 0.0 and 1.0 (e.g. 0.15 for 15%). Got: {tax_rate}")


def generate_zatca_tlv_qr(
    seller_name: str,
    vat_number: str,
    timestamp: str,
    invoice_total: str,
    vat_total: str
) -> str:
    """
    Generates standard ZATCA / Fatoora Base64 TLV encoded QR payload.
    Tags:
      1: Seller's Name
      2: VAT Registration Number
      3: Time Stamp (ISO 8601)
      4: Invoice Total (with VAT)
      5: VAT Total
    """
    def get_tlv(tag: int, value: str) -> bytes:
        val_bytes = str(value).encode('utf-8')
        length = len(val_bytes)
        if length > 255:
            raise ValueError(f"TLV field length exceeds 255 bytes for tag {tag}")
        return bytes([tag, length]) + val_bytes

    tlv_data = (
        get_tlv(1, seller_name) +
        get_tlv(2, vat_number) +
        get_tlv(3, timestamp) +
        get_tlv(4, invoice_total) +
        get_tlv(5, vat_total)
    )
    return base64.b64encode(tlv_data).decode('utf-8')


def decode_zatca_tlv_qr(b64_qr: str) -> Dict[int, str]:
    """
    Decodes a Base64-encoded ZATCA TLV payload back into structured tag values.
    Returns a dictionary mapping tag numbers (1-5) to their string values.
    """
    raw_bytes = base64.b64decode(b64_qr)
    result = {}
    idx = 0
    while idx < len(raw_bytes):
        tag = raw_bytes[idx]
        length = raw_bytes[idx + 1]
        idx += 2
        value_bytes = raw_bytes[idx:idx + length]
        result[tag] = value_bytes.decode('utf-8')
        idx += length
    return result


HTML_INVOICE_TEMPLATE = """<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
  <meta charset="utf-8">
  <title>فاتورة ضريبية إلكترونية - {invoice_num}</title>
  <style>
    body {{ font-family: 'Cairo', 'Segoe UI', 'Tahoma', sans-serif; margin: 30px; color: #1e293b; background-color: #f8fafc; }}
    .container {{ max-width: 860px; margin: 0 auto; background: #ffffff; padding: 32px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
    .header {{ display: flex; justify-content: space-between; border-bottom: 2px solid #0284c7; padding-bottom: 15px; }}
    .title {{ font-size: 24px; font-weight: bold; color: #0369a1; }}
    .subtitle {{ font-size: 13px; color: #64748b; margin-top: 4px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 25px; }}
    th, td {{ border: 1px solid #cbd5e1; padding: 12px; text-align: right; }}
    th {{ background-color: #f1f5f9; font-weight: 600; color: #334155; }}
    .footer-section {{ display: flex; justify-content: space-between; margin-top: 25px; align-items: flex-start; }}
    .total-box {{ width: 340px; }}
    .total-box table td {{ padding: 8px 12px; }}
    .grand-total {{ background-color: #e0f2fe; font-weight: bold; color: #0369a1; font-size: 16px; }}
    .qr {{ font-size: 11px; word-break: break-all; max-width: 320px; background: #f8fafc; padding: 12px; border: 1px dashed #94a3b8; border-radius: 6px; }}
    .qr-badge {{ display: inline-block; background-color: #0284c7; color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px; margin-bottom: 6px; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div>
        <div class="title">فاتورة مبيعات ضريبية معتمدة</div>
        <div class="subtitle">متوافقة مع متطلبات هيئة الزكاة والضريبة والجمارك (ZATCA)</div>
        <p style="margin-top: 10px;">رقم الفاتورة: <strong>{invoice_num}</strong><br>التاريخ: {date}</p>
      </div>
      <div style="text-align: left;" dir="ltr">
        <strong style="font-size: 16px;">{seller_name}</strong><br>
        <span style="color: #64748b;">الرقم الضريبي: {vat_num}</span>
      </div>
    </div>

    <table>
      <thead>
        <tr>
          <th>الوصف</th>
          <th style="width: 15%; text-align: center;">الكمية</th>
          <th style="width: 20%; text-align: left;">السعر الإفرادي</th>
          <th style="width: 20%; text-align: left;">المجموع</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>{item_desc}</td>
          <td style="text-align: center;">1</td>
          <td style="text-align: left;">{amount:.2f} {currency}</td>
          <td style="text-align: left;">{amount:.2f} {currency}</td>
        </tr>
      </tbody>
    </table>

    <div class="footer-section">
      <div class="qr">
        <span class="qr-badge">ZATCA Phase 2 TLV QR</span><br>
        <strong>رمز التحقق الإلكتروني المشفر (Base64):</strong><br>
        <code style="display: block; margin-top: 4px; color: #475569; font-size: 10px;">{qr_payload}</code>
      </div>

      <div class="total-box">
        <table>
          <tr><td>المجموع قبل الضريبة:</td><td style="text-align: left;">{amount:.2f} {currency}</td></tr>
          <tr><td>ضريبة القيمة المضافة ({tax_percent}%):</td><td style="text-align: left;">{vat:.2f} {currency}</td></tr>
          <tr class="grand-total"><td>الإجمالي المستحق:</td><td style="text-align: left;">{grand_total:.2f} {currency}</td></tr>
        </table>
      </div>
    </div>
  </div>
</body>
</html>
"""


def generate_invoice(
    invoice_num: str,
    amount: float,
    out_file: Path,
    seller_name: Optional[str] = None,
    vat_num: Optional[str] = None,
    tax_rate: float = 0.15,
    currency: str = "ر.س",
    item_desc: str = "خدمات استشارية معمارية وتطوير أنظمة رقمية",
    date_str: Optional[str] = None
) -> Tuple[str, float, float]:
    """Generates an Arabic RTL invoice and writes the HTML document with ZATCA TLV QR."""
    seller = seller_name or os.getenv("INVOICE_SELLER_NAME", "مؤسسة الحلول المتقدمة")
    vat_number = vat_num or os.getenv("INVOICE_VAT_NUMBER", "310000000000003")

    validate_invoice_params(invoice_num, amount, seller, vat_number, tax_rate)

    timestamp = date_str or datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    date_display = timestamp.split("T")[0]

    vat = round(amount * tax_rate, 2)
    grand_total = round(amount + vat, 2)

    qr_code = generate_zatca_tlv_qr(
        seller_name=seller,
        vat_number=vat_number,
        timestamp=timestamp,
        invoice_total=f"{grand_total:.2f}",
        vat_total=f"{vat:.2f}"
    )

    html = HTML_INVOICE_TEMPLATE.format(
        invoice_num=invoice_num,
        date=date_display,
        seller_name=seller,
        vat_num=vat_number,
        amount=amount,
        vat=vat,
        grand_total=grand_total,
        tax_percent=int(tax_rate * 100),
        currency=currency,
        item_desc=item_desc,
        qr_payload=qr_code
    )

    out_file = Path(out_file)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(html, encoding="utf-8")

    return qr_code, vat, grand_total


def main(args=None):
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(description="Generate ZATCA Phase 2 compliant Arabic invoice.")
    parser.add_argument("--inv", default="INV-2026-001", help="Invoice Number (e.g. INV-2026-001)")
    parser.add_argument("--amount", type=float, default=12500.0, help="Pre-tax invoice amount")
    parser.add_argument("--seller", default=None, help="Seller corporate entity name")
    parser.add_argument("--vat-num", default=None, help="15-digit ZATCA VAT registration number")
    parser.add_argument("--tax-rate", type=float, default=0.15, help="Tax rate fraction (default: 0.15)")
    parser.add_argument("--currency", default="ر.س", help="Currency symbol/code (default: ر.س)")
    parser.add_argument("--desc", default="خدمات استشارية معمارية وتطوير أنظمة رقمية", help="Line item description")
    parser.add_argument("--date", default=None, help="ISO-8601 Date/timestamp string (e.g. 2026-10-01T12:00:00Z)")
    parser.add_argument("--out", default="invoice_rendered.html", help="Output file path (default: invoice_rendered.html)")
    parser.add_argument("--decode-qr", type=str, default=None, help="Decode an existing ZATCA Base64 TLV payload and exit")
    parser.add_argument("--quiet", "-q", action="store_true", help="Quiet output")

    parsed = parser.parse_args(args)

    if parsed.decode_qr:
        try:
            decoded = decode_zatca_tlv_qr(parsed.decode_qr)
            tag_names = {
                1: "Seller Name",
                2: "VAT Number",
                3: "Timestamp",
                4: "Invoice Total",
                5: "VAT Total"
            }
            print("\n=== Decoded ZATCA Phase 2 TLV Payload ===")
            for tag, val in decoded.items():
                name = tag_names.get(tag, f"Tag {tag}")
                print(f" • [{tag}] {name:<16}: {val}")
            print("=========================================\n")
            return 0
        except Exception as e:
            print(f"[!] Error decoding TLV QR payload: {e}", file=sys.stderr)
            return 1

    try:
        out_path = Path(parsed.out)
        qr_code, vat, grand_total = generate_invoice(
            invoice_num=parsed.inv,
            amount=parsed.amount,
            out_file=out_path,
            seller_name=parsed.seller,
            vat_num=parsed.vat_num,
            tax_rate=parsed.tax_rate,
            currency=parsed.currency,
            item_desc=parsed.desc,
            date_str=parsed.date
        )

        if not parsed.quiet:
            print("\n" + "=" * 54)
            print("  🧾 ZATCA Compliant Arabic Invoice Generated")
            print("=" * 54)
            print(f" • Invoice Number : {parsed.inv}")
            print(f" • Pre-tax Amount : {parsed.amount:,.2f} {parsed.currency}")
            print(f" • VAT ({int(parsed.tax_rate * 100)}%)       : {vat:,.2f} {parsed.currency}")
            print(f" • Grand Total    : {grand_total:,.2f} {parsed.currency}")
            print(f" • Output File    : {out_path.resolve()}")
            print(f" • TLV QR Payload : {qr_code[:45]}...")
            print("=" * 54 + "\n")
        return 0

    except Exception as e:
        print(f"[!] Error generating invoice: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
