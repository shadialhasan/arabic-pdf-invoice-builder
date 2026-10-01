# -*- coding: utf-8 -*-
"""
Automated Test Suite for arabic-pdf-invoice-builder
Author: Eng. MHD. Shadi AL-Hasan <mhd.shadi.alhasan@gmail.com>
"""

import io
import sys
import unittest
import base64
from pathlib import Path
from tempfile import TemporaryDirectory

from invoice_builder import (
    generate_zatca_tlv_qr,
    decode_zatca_tlv_qr,
    validate_vat_number,
    validate_invoice_params,
    generate_invoice,
    main
)


class TestZatcaTlvQr(unittest.TestCase):

    def setUp(self):
        self.seller = "مؤسسة الحلول المتقدمة"
        self.vat = "310000000000003"
        self.timestamp = "2026-10-01T12:00:00Z"
        self.invoice_total = "14375.00"
        self.vat_total = "1875.00"

    def test_generate_and_decode_roundtrip(self):
        qr_b64 = generate_zatca_tlv_qr(
            seller_name=self.seller,
            vat_number=self.vat,
            timestamp=self.timestamp,
            invoice_total=self.invoice_total,
            vat_total=self.vat_total
        )
        self.assertIsInstance(qr_b64, str)
        self.assertTrue(len(qr_b64) > 20)

        # Decode and verify exact field match
        decoded = decode_zatca_tlv_qr(qr_b64)
        self.assertEqual(decoded[1], self.seller)
        self.assertEqual(decoded[2], self.vat)
        self.assertEqual(decoded[3], self.timestamp)
        self.assertEqual(decoded[4], self.invoice_total)
        self.assertEqual(decoded[5], self.vat_total)

    def test_tlv_binary_structure(self):
        qr_b64 = generate_zatca_tlv_qr(
            seller_name="Test",
            vat_number="300000000000003",
            timestamp="2026-10-01",
            invoice_total="100.00",
            vat_total="15.00"
        )
        raw_bytes = base64.b64decode(qr_b64)
        # First byte must be tag 1
        self.assertEqual(raw_bytes[0], 1)
        # Second byte is length of "Test" (4)
        self.assertEqual(raw_bytes[1], 4)
        # Value is b"Test"
        self.assertEqual(raw_bytes[2:6], b"Test")


class TestValidation(unittest.TestCase):

    def test_validate_vat_number(self):
        # Standard KSA 15-digit VAT starting and ending with 3
        self.assertTrue(validate_vat_number("310000000000003"))
        # Generic 15-digit
        self.assertTrue(validate_vat_number("123456789012345"))
        # Invalid VAT numbers
        self.assertFalse(validate_vat_number("12345"))
        self.assertFalse(validate_vat_number("31000000000000A"))
        self.assertFalse(validate_vat_number(""))
        self.assertFalse(validate_vat_number(None)) # type: ignore

    def test_validate_invoice_params(self):
        # Valid params should not raise
        validate_invoice_params("INV-001", 100.0, "Seller", "310000000000003", 0.15)

        # Empty invoice number
        with self.assertRaises(ValueError):
            validate_invoice_params("", 100.0, "Seller", "310000000000003")

        # Zero or negative amount
        with self.assertRaises(ValueError):
            validate_invoice_params("INV-001", 0.0, "Seller", "310000000000003")
        with self.assertRaises(ValueError):
            validate_invoice_params("INV-001", -50.0, "Seller", "310000000000003")

        # Invalid tax rate
        with self.assertRaises(ValueError):
            validate_invoice_params("INV-001", 100.0, "Seller", "310000000000003", tax_rate=1.5)


class TestInvoiceGeneration(unittest.TestCase):

    def test_generate_invoice_html(self):
        with TemporaryDirectory() as tmpdir:
            out_file = Path(tmpdir) / "output_test_invoice.html"
            qr, vat, grand = generate_invoice(
                invoice_num="INV-2026-TEST",
                amount=1000.0,
                out_file=out_file,
                seller_name="شركة التقنية العربية",
                vat_num="310000000000003",
                tax_rate=0.15,
                currency="ر.س"
            )

            self.assertEqual(vat, 150.0)
            self.assertEqual(grand, 1150.0)
            self.assertTrue(out_file.exists())

            content = out_file.read_text(encoding="utf-8")
            self.assertIn('dir="rtl"', content)
            self.assertIn("INV-2026-TEST", content)
            self.assertIn("شركة التقنية العربية", content)
            self.assertIn("1150.00 ر.س", content)
            self.assertIn(qr, content)


class TestInvoiceCLI(unittest.TestCase):

    def test_cli_success(self):
        with TemporaryDirectory() as tmpdir:
            out_file = Path(tmpdir) / "cli_invoice.html"
            code = main([
                "--inv", "INV-CLI-01",
                "--amount", "5000",
                "--out", str(out_file),
                "--quiet"
            ])
            self.assertEqual(code, 0)
            self.assertTrue(out_file.exists())

    def test_cli_decode_qr(self):
        # Generate a QR string first
        qr_code = generate_zatca_tlv_qr(
            seller_name="CLI Company",
            vat_number="310000000000003",
            timestamp="2026-10-01T10:00:00Z",
            invoice_total="115.00",
            vat_total="15.00"
        )
        stdout_buf = io.StringIO()
        old_stdout = sys.stdout
        try:
            sys.stdout = stdout_buf
            code = main(["--decode-qr", qr_code])
            self.assertEqual(code, 0)
            output = stdout_buf.getvalue()
            self.assertIn("CLI Company", output)
            self.assertIn("310000000000003", output)
        finally:
            sys.stdout = old_stdout

    def test_cli_invalid_amount(self):
        stderr_buf = io.StringIO()
        old_stderr = sys.stderr
        try:
            sys.stderr = stderr_buf
            code = main(["--amount", "-100"])
            self.assertEqual(code, 1)
        finally:
            sys.stderr = old_stderr


if __name__ == "__main__":
    unittest.main()
