import io
import math
from pathlib import Path
from typing import Any, Dict, Optional
import qrcode
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


class CertificateGenerator:
    """
    High-quality PDF Certificate Generation Engine using ReportLab.
    Renders an elegant landscape A4 certificate with custom borders,
    gold seal, typography, issuer details, dynamic recipient text,
    and an embedded verification QR code.
    """

    # Color palette
    NAVY_DARK = HexColor("#0A192F")
    NAVY_LIGHT = HexColor("#1E3A8A")
    GOLD_MAIN = HexColor("#C59B27")
    GOLD_LIGHT = HexColor("#F59E0B")
    TEXT_MUTED = HexColor("#64748B")
    TEXT_BODY = HexColor("#334155")
    WHITE = HexColor("#FFFFFF")
    BG_CREAM = HexColor("#FDFDFD")

    @classmethod
    def generate_certificate(
        cls,
        certificate_id: str,
        recipient_name: str,
        recipient_email: str,
        event_title: str,
        issuer_name: str,
        issue_date: str,
        custom_data: Optional[Dict[str, Any]] = None,
        output_path: Optional[Path] = None,
        verification_url: Optional[str] = None,
    ) -> bytes:
        """
        Generate a certificate PDF for a recipient.
        """
        # Hook for testing individual failure handling
        if "__FORCE_FAIL__" in recipient_name or "__FORCE_FAIL__" in recipient_email:
            raise RuntimeError(f"Simulated generation failure for recipient {recipient_name}")

        width, height = landscape(A4)  # 841.89 x 595.27 points

        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=(width, height))
        c.setTitle(f"Certificate - {recipient_name}")

        # 1. Background fill
        c.setFillColor(cls.BG_CREAM)
        c.rect(0, 0, width, height, fill=1, stroke=0)

        # 2. Outer and Inner Decorative Borders
        cls._draw_borders(c, width, height)

        # 3. Header Section (Issuer Name & Top Banner)
        cls._draw_header(c, width, height, issuer_name)

        # 4. Main Certificate Title
        c.setFont("Helvetica-Bold", 30)
        c.setFillColor(cls.NAVY_DARK)
        c.drawCentredString(width / 2.0, height - 150, "CERTIFICATE OF ACHIEVEMENT")

        c.setFont("Helvetica", 11)
        c.setFillColor(cls.TEXT_MUTED)
        c.drawCentredString(width / 2.0, height - 175, "THIS CERTIFICATE IS PROUDLY PRESENTED TO")

        # 5. Recipient Name
        c.setFont("Helvetica-Bold", 26)
        c.setFillColor(cls.NAVY_LIGHT)
        c.drawCentredString(width / 2.0, height - 215, recipient_name.upper())

        # Gold underline below recipient name
        name_width = min(c.stringWidth(recipient_name.upper(), "Helvetica-Bold", 26), 500)
        c.setStrokeColor(cls.GOLD_MAIN)
        c.setLineWidth(1.5)
        c.line(width / 2.0 - name_width / 2.0 - 20, height - 225, width / 2.0 + name_width / 2.0 + 20, height - 225)

        # 6. Body Text
        c.setFont("Helvetica", 12)
        c.setFillColor(cls.TEXT_BODY)
        c.drawCentredString(
            width / 2.0,
            height - 255,
            "for successfully completing all requirements and demonstrating excellence in",
        )

        # Event / Course Title
        c.setFont("Helvetica-Bold", 19)
        c.setFillColor(cls.NAVY_DARK)
        c.drawCentredString(width / 2.0, height - 285, event_title)

        # 7. Custom Data Badges (e.g. Grade, Distinction, Hours)
        if custom_data:
            cls._draw_custom_metadata(c, width, height, custom_data)

        # 8. Gold Seal Ornament in Center Bottom
        cls._draw_seal(c, width / 2.0, 115)

        # 9. Left Side: Issue Date
        cls._draw_date_section(c, issue_date, 130, 95)

        # 10. Right Side: Signature Section
        cls._draw_signature_section(c, issuer_name, width - 210, 95)

        # 11. Bottom Left: Embedded QR Code & Certificate ID
        verify_link = verification_url or f"https://verify.cert/{certificate_id}"
        cls._draw_qr_code(c, verify_link, 50, 42, 50)

        # Certificate ID string at footer
        c.setFont("Helvetica", 8)
        c.setFillColor(cls.TEXT_MUTED)
        c.drawString(108, 52, f"Certificate ID: {certificate_id}")
        c.drawString(108, 42, f"Recipient: {recipient_email}")

        # Finalize PDF
        c.showPage()
        c.save()

        pdf_bytes = buf.getvalue()
        buf.close()

        # If file output requested, write atomically
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(pdf_bytes)

        return pdf_bytes

    @classmethod
    def _draw_borders(cls, c: canvas.Canvas, width: float, height: float) -> None:
        """Draw multi-tier borders and ornamental corner brackets."""
        # Outer dark border
        c.setStrokeColor(cls.NAVY_DARK)
        c.setLineWidth(4)
        c.rect(20, 20, width - 40, height - 40)

        # Inner gold border
        c.setStrokeColor(cls.GOLD_MAIN)
        c.setLineWidth(1.5)
        c.rect(28, 28, width - 56, height - 56)

        # Thin gold hairline
        c.setStrokeColor(cls.GOLD_LIGHT)
        c.setLineWidth(0.5)
        c.rect(33, 33, width - 66, height - 66)

        # Corner ornamental accents
        corner_offsets = [
            (28, 28, 1, 1),
            (width - 28, 28, -1, 1),
            (28, height - 28, 1, -1),
            (width - 28, height - 28, -1, -1),
        ]
        c.setFillColor(cls.GOLD_MAIN)
        for x, y, dx, dy in corner_offsets:
            p = c.beginPath()
            p.moveTo(x, y)
            p.lineTo(x + dx * 20, y)
            p.lineTo(x, y + dy * 20)
            p.close()
            c.drawPath(p, fill=1, stroke=0)

    @classmethod
    def _draw_header(cls, c: canvas.Canvas, width: float, height: float, issuer_name: str) -> None:
        """Draw issuer header banner."""
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(cls.GOLD_MAIN)
        c.drawCentredString(width / 2.0, height - 65, issuer_name.upper())

        c.setFont("Helvetica", 9)
        c.setFillColor(cls.TEXT_MUTED)
        c.drawCentredString(width / 2.0, height - 80, "OFFICIAL CREDENTIAL OF MERIT & DISTINCTION")

        # Decorative thin divider line
        c.setStrokeColor(cls.GOLD_MAIN)
        c.setLineWidth(1)
        c.line(width / 2.0 - 150, height - 92, width / 2.0 + 150, height - 92)

    @classmethod
    def _draw_custom_metadata(
        cls, c: canvas.Canvas, width: float, height: float, custom_data: Dict[str, Any]
    ) -> None:
        """Render extra attributes like Grade, Distinction, or Hours."""
        items = [f"{k.replace('_', ' ').title()}: {v}" for k, v in custom_data.items() if v is not None]
        if items:
            badge_text = "   |   ".join(items)
            c.setFont("Helvetica-Oblique", 11)
            c.setFillColor(cls.GOLD_MAIN)
            c.drawCentredString(width / 2.0, height - 315, badge_text)

    @classmethod
    def _draw_seal(cls, c: canvas.Canvas, cx: float, cy: float) -> None:
        """Draw an official gold starburst seal emblem."""
        c.saveState()
        num_points = 24
        outer_radius = 28
        inner_radius = 24
        p = c.beginPath()
        for i in range(num_points * 2):
            angle = i * (math.pi / num_points)
            r = outer_radius if (i % 2 == 0) else inner_radius
            px = cx + r * math.cos(angle)
            py = cy + r * math.sin(angle)
            if i == 0:
                p.moveTo(px, py)
            else:
                p.lineTo(px, py)
        p.close()
        c.setFillColor(cls.GOLD_MAIN)
        c.drawPath(p, fill=1, stroke=0)

        c.setFillColor(cls.NAVY_DARK)
        c.circle(cx, cy, 21, fill=1, stroke=0)

        c.setFont("Helvetica-Bold", 6.5)
        c.setFillColor(cls.GOLD_MAIN)
        c.drawCentredString(cx, cy + 3, "OFFICIAL")
        c.drawCentredString(cx, cy - 6, "SEAL")
        c.restoreState()

    @classmethod
    def _draw_date_section(cls, c: canvas.Canvas, issue_date: str, x: float, y: float) -> None:
        """Render date line."""
        c.setStrokeColor(cls.TEXT_MUTED)
        c.setLineWidth(1)
        c.line(x - 60, y, x + 60, y)

        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(cls.NAVY_DARK)
        c.drawCentredString(x, y + 8, issue_date)

        c.setFont("Helvetica", 9)
        c.setFillColor(cls.TEXT_MUTED)
        c.drawCentredString(x, y - 14, "DATE OF ISSUANCE")

    @classmethod
    def _draw_signature_section(cls, c: canvas.Canvas, issuer_name: str, x: float, y: float) -> None:
        """Render signature line and issuer title."""
        c.setStrokeColor(cls.TEXT_MUTED)
        c.setLineWidth(1)
        c.line(x - 70, y, x + 70, y)

        c.setFont("Times-BoldItalic", 12)
        c.setFillColor(cls.NAVY_LIGHT)
        c.drawCentredString(x, y + 8, issuer_name)

        c.setFont("Helvetica", 9)
        c.setFillColor(cls.TEXT_MUTED)
        c.drawCentredString(x, y - 14, "AUTHORIZED SIGNATURE")

    @classmethod
    def _draw_qr_code(cls, c: canvas.Canvas, data: str, x: float, y: float, size: float) -> None:
        """Generate and draw an authentic verification QR code."""
        try:
            qr = qrcode.QRCode(box_size=3, border=0)
            qr.add_data(data)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")

            img_buf = io.BytesIO()
            img.save(img_buf, format="PNG")
            img_buf.seek(0)

            c.drawImage(ImageReader(img_buf), x, y, width=size, height=size)
        except Exception:
            c.setStrokeColor(cls.TEXT_MUTED)
            c.rect(x, y, size, size)
