import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

TEMPLATES = {
    "classic": {
        "bg": colors.HexColor("#fffef5"),
        "border": colors.HexColor("#c9a227"),
        "accent": colors.HexColor("#1a1a2e"),
        "subtitle": colors.HexColor("#555555"),
    },
    "modern": {
        "bg": colors.HexColor("#f0f4f8"),
        "border": colors.HexColor("#2563eb"),
        "accent": colors.HexColor("#1e293b"),
        "subtitle": colors.HexColor("#64748b"),
    },
    "elegant": {
        "bg": colors.HexColor("#fdf2f8"),
        "border": colors.HexColor("#9d174d"),
        "accent": colors.HexColor("#831843"),
        "subtitle": colors.HexColor("#6b7280"),
    },
}

VALID_TEMPLATES = set(TEMPLATES.keys())


def completion_text(cert, batch):
    course = (cert.get("course") or "").strip()
    title = (batch.get("title") or "").strip()
    if course:
        return f"has successfully completed {course}"
    return f"has successfully completed {title}"


def generate_pdf(cert, batch):
    buf = io.BytesIO()
    w, h = landscape(A4)
    c = canvas.Canvas(buf, pagesize=landscape(A4))

    template = batch.get("template", "classic")
    tpl = TEMPLATES.get(template, TEMPLATES["classic"])

    c.setFillColor(tpl["bg"])
    c.rect(0, 0, w, h, fill=1, stroke=0)

    margin = 0.5 * inch
    c.setStrokeColor(tpl["border"])
    c.setLineWidth(3)
    c.rect(margin, margin, w - 2 * margin, h - 2 * margin, fill=0, stroke=1)
    c.setLineWidth(1)
    c.rect(margin + 8, margin + 8, w - 2 * margin - 16, h - 2 * margin - 16, fill=0, stroke=1)

    y = h - 1.4 * inch

    c.setFillColor(tpl["accent"])
    c.setFont("Helvetica-Bold", 36)
    c.drawCentredString(w / 2, y, "CERTIFICATE")

    y -= 0.5 * inch
    c.setFillColor(tpl["subtitle"])
    c.setFont("Helvetica", 14)
    c.drawCentredString(w / 2, y, "of Achievement")

    program = (batch.get("title") or "").strip()
    course = (cert.get("course") or "").strip()
    if program and course:
        y -= 0.45 * inch
        c.setFont("Helvetica-Oblique", 12)
        c.drawCentredString(w / 2, y, program)

    y -= 0.7 * inch
    c.setFont("Helvetica", 13)
    c.drawCentredString(w / 2, y, "This is to certify that")

    y -= 0.7 * inch
    c.setFillColor(tpl["accent"])
    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(w / 2, y, cert["student_name"])

    y -= 0.7 * inch
    c.setFillColor(tpl["subtitle"])
    c.setFont("Helvetica", 13)
    c.drawCentredString(w / 2, y, completion_text(cert, batch))

    y -= 0.6 * inch
    c.setFont("Helvetica", 11)
    c.drawCentredString(w / 2, y, f"awarded by {batch['company_name']}")

    date_str = (cert.get("date") or "").strip()
    if date_str:
        y -= 0.6 * inch
        c.drawCentredString(w / 2, y, f"Date: {date_str}")

    c.setFont("Helvetica", 8)
    c.setFillColor(tpl["subtitle"])
    c.drawCentredString(w / 2, margin + 0.3 * inch, f"Certificate ID: {cert['unique_id']}")

    c.showPage()
    c.save()
    buf.seek(0)
    return buf
