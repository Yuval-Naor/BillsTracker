from fastapi import APIRouter, Depends
from datetime import datetime
from app.auth import get_current_user
from app.database import SessionLocal
from app import models, schemas
from app.services import gmail_service, pdf_service, image_service, html_service, openai_service, storage_service
from app.celery_app import celery_app

router = APIRouter()

@router.post("/sync")
def sync_gmail_background(current_user: models.User = Depends(get_current_user)):
    celery_app.send_task("app.tasks.sync_gmail_inbox", args=[current_user.id])
    return {"message": "Gmail sync initiated"}

@router.get("/bills", response_model=list[schemas.BillOut])
def list_bills(current_user: models.User = Depends(get_current_user)):
    db = SessionLocal()
    bills = db.query(models.Bill).filter(models.Bill.user_id == current_user.id).all()
    db.close()
    return bills

@celery_app.task(name="app.tasks.sync_gmail_inbox")
def sync_gmail_inbox(user_id: int):
    db = SessionLocal()
    user = db.query(models.User).get(user_id)
    if not user:
        db.close()
        return "User not found"
    try:
        access_token = gmail_service.refresh_access_token(user.google_refresh_token)
    except Exception as e:
        print(f"Token refresh failed for {user.email}: {e}")
        db.close()
        return "Token refresh failed"
    query = 'has:attachment OR subject:(bill OR invoice OR חשבונית OR קבלה)'
    try:
        message_ids = gmail_service.list_message_ids(access_token, query=query, max_results=50)
    except Exception as e:
        print(f"Gmail API error for {user.email}: {e}")
        db.close()
        return "Gmail API error"
    
    for msg_id in message_ids:
        if db.query(models.Bill).filter_by(user_id=user.id, message_id=msg_id).first():
            continue
        try:
            message = gmail_service.get_message(access_token, msg_id)
        except Exception as e:
            print(f"Failed to fetch message {msg_id}: {e}")
            continue
        full_text_segments = []

        payload = message.get("payload", {})
        if payload.get("body", {}).get("data"):
            import base64
            body_text = base64.urlsafe_b64decode(payload["body"]["data"] + "==").decode("utf-8", errors="ignore")
            full_text_segments.append(body_text)
            urls = gmail_service.extract_urls_from_text(body_text)
        else:
            urls = []

        attachments = gmail_service.get_attachments_info(message)
        for attach in attachments:
            att_id = attach["attachmentId"]
            filename = attach["filename"]
            mime = attach["mimeType"]
            try:
                data = gmail_service.download_attachment(access_token, msg_id, att_id)
            except Exception as e:
                print(f"Attachment download failed for {filename}: {e}")
                continue
            if filename.lower().endswith(".pdf") or mime == "application/pdf":
                pdf_text = pdf_service.extract_text_from_pdf(data)
                full_text_segments.append(pdf_text)
            elif mime in ["image/jpeg", "image/png"]:
                ocr_text = image_service.extract_text_from_image(data)
                full_text_segments.append(ocr_text)

        for url in urls:
            try:
                import requests
                resp = requests.get(url, timeout=10)
                content_type = resp.headers.get("Content-Type", "")
                if "application/pdf" in content_type or url.lower().endswith(".pdf"):
                    pdf_text = pdf_service.extract_text_from_pdf(resp.content)
                    full_text_segments.append(pdf_text)
                elif "text/html" in content_type:
                    html_text = html_service.extract_text_from_html(resp.text)
                    full_text_segments.append(html_text)
            except Exception as e:
                print(f"Failed to fetch URL {url}: {e}")
                continue

        if not full_text_segments:
            continue
        combined_text = "\n".join(full_text_segments)
        bill_data = openai_service.extract_bill_data(combined_text)
        if not bill_data:
            continue
        bill = models.Bill(
            user_id=user.id,
            message_id=msg_id,
            vendor=bill_data.get("vendor"),
            date=bill_data.get("date"),
            due_date=bill_data.get("due_date"),
            amount=bill_data.get("amount"),
            currency=bill_data.get("currency"),
            category=bill_data.get("category"),
            status=bill_data.get("status"),
            blob_name=""
        )
        bill.paid = detect_paid_status(combined_text)
        db.add(bill)
        db.commit()
    db.close()
    return "Sync completed"

def detect_paid_status(bill_text: str) -> bool:
    paid_keywords = ["receipt", "payment confirmation", "קבלה", "אישור תשלום"]
    return any(keyword.lower() in bill_text.lower() for keyword in paid_keywords)
