import os
import io
import base64
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors

import resend

# ----------------- Config -----------------

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
RESEND_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "VyapaarAI <updates@vyapaarai.in>")

if not RESEND_API_KEY:
    raise RuntimeError("RESEND_API_KEY environment variable is required")

resend.api_key = RESEND_API_KEY

app = FastAPI()


# ----------------- Models (simple) -----------------

class Item(BaseModel):
    name: str
    quantity: int


class OrderPayload(BaseModel):
    items: List[Item]


# ----------------- Helpers -----------------
item_unit_price = 50
def _draw_box(c, x, y, w, h, fill_color=None, stroke_color=colors.black, stroke_width=1):
    """Small helper to draw a rectangle box."""
    c.setStrokeColor(stroke_color)
    c.setLineWidth(stroke_width)
    if fill_color:
        c.setFillColor(fill_color)
        c.rect(x, y, w, h, fill=1, stroke=1)
        c.setFillColor(colors.black)
    else:
        c.rect(x, y, w, h, fill=0, stroke=1)

def generate_invoice_pdf(
    customer_name: str,
    items: List[Item],
    order_id: str,
) -> bytes:
    """
    Cleaner, simpler invoice layout:

    Header:
      - Seller info
      - Tax Invoice title
      - Invoice No / Date / GSTIN

    Body:
      - Bill To
      - Items table: #, Item, Qty, Price/Unit, Amount
      - Grand total row

    Footer:
      - Amount in words (left)
      - Subtotal / Discount / Tax / Total / Received / Balance (right)
      - Company seal and sign box at bottom
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    left_margin = 40
    right_margin = 40
    usable_width = width - left_margin - right_margin
    y = height - 50

    # ---------- Seller header ----------
    c.setFont("Helvetica-Bold", 12)
    c.drawString(left_margin, y, "Amul Dairy")
    c.setFont("Helvetica", 10)
    y -= 14
    c.drawString(left_margin, y, "Address: Mumbai, Maharashtra, India")
    y -= 14
    c.drawString(left_margin, y, "Phone: +91-99999 99999   Email: support@amul.in")

    # Title
    y -= 30
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(left_margin + usable_width / 2, y, "Tax Invoice")

    # Invoice meta
    y -= 25
    c.setFont("Helvetica", 10)
    c.drawString(left_margin, y, f"Invoice No.: {order_id}")
    c.drawRightString(left_margin + usable_width, y,
                      f"Date: {datetime.utcnow().strftime('%d/%m/%Y')}")
    y -= 14
    c.drawRightString(left_margin + usable_width, y, "GSTIN: 27ABCDE1234F1Z5")

    # ---------- Bill To ----------
    y -= 30
    c.setFont("Helvetica-Bold", 11)
    c.drawString(left_margin, y, "Bill To:")
    y -= 14
    c.setFont("Helvetica", 10)
    c.drawString(left_margin + 10, y, customer_name)
    y -= 14
    c.drawString(left_margin + 10, y, "Address: Mumbai, Maharashtra, India")
    y -= 24

    # ---------- Items table ----------
    row_height = 18
    header_height = row_height

    # Column widths
    col_no_w = 30
    col_item_w = 230
    col_qty_w = 50
    col_price_w = 80
    col_amt_w = 80

    table_width = col_no_w + col_item_w + col_qty_w + col_price_w + col_amt_w
    table_x = left_margin
    table_y = y

    # Header background
    c.setFillColor(colors.HexColor("#f28c20"))
    c.rect(table_x, table_y - header_height, table_width, header_height, fill=1, stroke=0)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 9)

    header_y_text = table_y - header_height + 5
    x = table_x + 3
    c.drawString(x, header_y_text, "#")
    x += col_no_w
    c.drawString(x, header_y_text, "Item")
    x += col_item_w
    c.drawString(x, header_y_text, "Qty")
    x += col_qty_w
    c.drawString(x, header_y_text, "Price/Unit")
    x += col_price_w
    c.drawString(x, header_y_text, "Amount")

    # Rows
    c.setFont("Helvetica", 9)
    y = table_y - header_height - row_height
    grand_total = 0.0

    for idx, item in enumerate(items, start=1):
        # New page if needed
        if y < 100:
            c.showPage()
            # reset margins, header for new page
            y = height - 80
            table_x = left_margin
            table_y = y

            # Re-draw header
            c.setFillColor(colors.HexColor("#f28c20"))
            c.rect(table_x, table_y - header_height, table_width, header_height, fill=1, stroke=0)
            c.setFillColor(colors.black)
            c.setFont("Helvetica-Bold", 9)
            header_y_text = table_y - header_height + 5
            x = table_x + 3
            c.drawString(x, header_y_text, "#")
            x += col_no_w
            c.drawString(x, header_y_text, "Item")
            x += col_item_w
            c.drawString(x, header_y_text, "Qty")
            x += col_qty_w
            c.drawString(x, header_y_text, "Price/Unit")
            x += col_price_w
            c.drawString(x, header_y_text, "Amount")
            c.setFont("Helvetica", 9)
            y = table_y - header_height - row_height

        line_amount = item_unit_price * item.quantity
        grand_total += line_amount

        # Row border
        c.rect(table_x, y, table_width, row_height, fill=0, stroke=1)

        x = table_x + 3
        c.drawString(x, y + 5, str(idx))
        x += col_no_w
        c.drawString(x, y + 5, item.name[:30])
        x += col_item_w
        c.drawRightString(x + col_qty_w - 5, y + 5, str(item.quantity))
        x += col_qty_w
        c.drawRightString(x + col_price_w - 5, y + 5, f"{item_unit_price:,.2f}")
        x += col_price_w
        c.drawRightString(x + col_amt_w - 5, y + 5, f"{line_amount:,.2f}")

        y -= row_height

    # Total row
    c.setFillColor(colors.HexColor("#f28c20"))
    c.rect(table_x, y, table_width, row_height, fill=1, stroke=0)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 9)
    c.drawRightString(table_x + col_no_w + col_item_w + col_qty_w + col_price_w - 5,
                      y + 5, "Total")
    c.drawRightString(table_x + table_width - 5,
                      y + 5, f"{grand_total:,.2f}")

    # ---------- Summary & footer ----------
    y -= 40
    if y < 120:
        c.showPage()
        y = height - 100

    # Amount in words (left)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(left_margin, y, "Amount in words:")
    c.setFont("Helvetica", 9)
    y -= 14
    c.drawString(left_margin + 10, y, f"Rupees {grand_total:,.2f} only")

    # Totals box (right)
    box_width = 160
    box_height = 70
    box_x = left_margin + usable_width - box_width
    box_y = y - box_height + 50
    c.rect(box_x, box_y, box_width, box_height, fill=0, stroke=1)

    c.setFont("Helvetica-Bold", 10)
    c.drawString(box_x + 5, box_y + box_height - 15, "Total")
    c.setFont("Helvetica", 9)
    c.drawRightString(box_x + box_width - 5, box_y + box_height - 15,
                      f"{grand_total:,.2f}")

    c.drawString(box_x + 5, box_y + box_height - 30, "Received")
    c.drawRightString(box_x + box_width - 5, box_y + box_height - 30,
                      f"{grand_total:,.2f}")

    c.drawString(box_x + 5, box_y + box_height - 45, "Balance")
    c.drawRightString(box_x + box_width - 5, box_y + box_height - 45, "0.00")

    # Company seal & sign at bottom
    seal_y = box_y - 80
    if seal_y < 60:
        c.showPage()
        seal_y = height - 150

    seal_height = 60
    seal_width = usable_width * 0.5
    c.rect(left_margin, seal_y, seal_width, seal_height, fill=0, stroke=1)
    c.setFont("Helvetica", 9)
    c.drawCentredString(left_margin + seal_width / 2, seal_y + 10, "Company seal and Sign")

    c.showPage()
    c.save()

    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

def send_invoice_email(
    to_email: str,
    customer_name: str,
    items: List[Item],
    pdf_bytes: bytes,
    order_id: str,
) -> str:
    """
    Send the invoice PDF via Resend.
    Returns Resend message ID (if available).
    """
    pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")
    filename = f"invoice_{order_id}.pdf"

    # Simple text summary in the email body
    lines = []
    grand_total = 0.0
    for item in items:
        line_total = item_unit_price * item.quantity
        grand_total += line_total
        lines.append(
            f"{item.name} — ₹{item_unit_price:,.2f} x {item.quantity} = ₹{line_total:,.2f}"
        )

    html_body = f"""
    <p>Hi {customer_name},</p>
    <p>Thank you for your order!</p>
    <p><b>Order ID: {order_id}</b></p>
    <p>Order summary:</p>
    <ul>
        {''.join(f'<li>{l}</li>' for l in lines)}
    </ul>
    <p><b>Grand Total: ₹{grand_total:,.2f}</b></p>
    <p>Your invoice is attached as a PDF.</p>
    <p>Best regards,<br/>VyapaarAI</p>
    """

    email_params = {
        "from": RESEND_FROM_EMAIL,
        "to": [to_email],
        "subject": f"Order ID: {order_id} - VyapaarAI",
        "html": html_body,
        "attachments": [
            {
                "filename": filename,
                "content": pdf_base64,
                "contentType": "application/pdf",
            }
        ],
    }

    res = resend.Emails.send(email_params)
    if isinstance(res, dict):
        return res.get("id") or res.get("message_id", "")
    return getattr(res, "id", "")


# ----------------- Endpoint -----------------

@app.post("/place_order")
async def place_order(payload: OrderPayload):
    if not payload.items:
        raise HTTPException(status_code=400, detail="No items provided")

    customer_name = os.getenv("CUSTOMER_NAME", "John Doe")
    customer_email = os.getenv("CUSTOMER_EMAIL", "john.doe@example.com")

    # Simple "random" order id based on timestamp
    order_id = "ORD-" + datetime.utcnow().strftime("%Y%m%d%H%M%S")

    try:
        pdf_bytes = generate_invoice_pdf(
            customer_name=customer_name,
            items=payload.items,
            order_id=order_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {e}")

    try:
        message_id = send_invoice_email(
            to_email=customer_email,
            customer_name=customer_name,
            items=payload.items,
            pdf_bytes=pdf_bytes,
            order_id=order_id,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to send invoice email: {e}")

    return {
        "status": "ok",
        "message": "Invoice generated and sent via email.",
        "order_id": order_id,
        "resend_message_id": message_id,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
