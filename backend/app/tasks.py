from fastapi import APIRouter, Depends
from datetime import datetime
import traceback
from app.auth import get_current_user
from app.database import SessionLocal
from app import models, schemas
from app.services import gmail_service, pdf_service, image_service, html_service, openai_service, storage_service
from app.celery_app import celery_app
from loguru import logger
from typing import List, Dict, Any
from app.services.openai_service import extract_bills_data_from_batch, estimate_token_count

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

@router.get("/user/me")
def get_current_user_info(current_user: models.User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name
    }

@celery_app.task(name="app.tasks.sync_gmail_inbox")
def sync_gmail_inbox(user_id: int):
    logger.info(f"Starting Gmail sync for user ID {user_id}")
    db = SessionLocal()
    user = db.query(models.User).get(user_id)
    if not user:
        logger.error(f"User ID {user_id} not found in database")
        db.close()
        return "User not found"
    
    # Check if refresh token exists
    if not user.google_refresh_token:
        logger.error(f"No refresh token stored for user {user.email}")
        db.close()
        return "No refresh token available"
    
    try:
        logger.info(f"Refreshing access token for {user.email}")
        access_token = gmail_service.refresh_access_token(user.google_refresh_token)
        logger.info(f"Successfully obtained access token")
    except Exception as e:
        logger.error(f"Token refresh failed for {user.email}: {str(e)}")
        logger.error(traceback.format_exc())
        db.close()
        return f"Token refresh failed: {str(e)}"
    
    query = 'has:attachment OR subject:(bill OR invoice OR חשבונית OR קבלה)'
    try:
        logger.info(f"Fetching messages with query: {query}")
        # Enhanced query with more Hebrew bill-related terms
        query = 'has:attachment OR subject:(bill OR invoice OR receipt OR payment OR חשבונית OR קבלה OR חשבון OR ארנונה OR מים OR גז OR חשמל OR לתשלום OR תשלום OR תשלומים OR חיוב OR tax)'
        message_ids = gmail_service.list_message_ids(access_token, query=query, max_results=50)
        if not message_ids:
            logger.info(f"No messages found for {user.email}")
            db.close()
            return "No messages found"
        logger.info(f"Found {len(message_ids)} messages")
    except Exception as e:
        error_msg = f"Gmail API error for {user.email}: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        db.close()
        return f"Gmail API error: {str(e)}"
    
    # First, filter out already processed messages
    existing_message_ids = {
        result[0] for result in 
        db.query(models.Bill.message_id).filter(
            models.Bill.user_id==user.id, 
            models.Bill.message_id.in_(message_ids)
        ).all()
    }
    
    new_message_ids = [msg_id for msg_id in message_ids if msg_id not in existing_message_ids]
    logger.info(f"Found {len(new_message_ids)} new messages to process")
    
    if not new_message_ids:
        db.close()
        return "No new messages to process"
    
    batch_texts = []
    batch_metadata = []
    current_batch_tokens = 0
    max_tokens_per_batch = 6000  # Safe threshold under 8000 tokens/minute limit

    for msg_id in new_message_ids:
        try:
            message = gmail_service.get_message(access_token, msg_id)
            full_text_segments = []
            
            # Extract message body
            payload = message.get("payload", {})
            if payload.get("body", {}).get("data"):
                import base64
                body_text = base64.urlsafe_b64decode(payload["body"]["data"] + "==").decode("utf-8", errors="ignore")
                full_text_segments.append(body_text)
                urls = gmail_service.extract_urls_from_text(body_text)
            else:
                urls = []
            
            # Process attachments
            attachments = gmail_service.get_attachments_info(message)
            for attach in attachments:
                att_id = attach["attachmentId"]
                filename = attach["filename"]
                mime = attach["mimeType"]
                try:
                    data = gmail_service.download_attachment(access_token, msg_id, att_id)
                except Exception as e:
                    logger.error(f"Attachment download failed for {filename}: {str(e)}")
                    continue
                
                if filename.lower().endswith(".pdf") or mime == "application/pdf":
                    pdf_text = pdf_service.extract_text_from_pdf(data)
                    if pdf_text:
                        full_text_segments.append(pdf_text)
                elif mime in ["image/jpeg", "image/png"]:
                    ocr_text = image_service.extract_text_from_image(data)
                    if ocr_text:
                        full_text_segments.append(ocr_text)
            
            # Process URLs in the email
            for url in urls:
                try:
                    import requests
                    resp = requests.get(url, timeout=10)
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/pdf" in content_type or url.lower().endswith(".pdf"):
                        pdf_text = pdf_service.extract_text_from_pdf(resp.content)
                        if pdf_text:
                            full_text_segments.append(pdf_text)
                    elif "text/html" in content_type:
                        html_text = html_service.extract_text_from_html(resp.text)
                        if html_text:
                            full_text_segments.append(html_text)
                except Exception as e:
                    logger.error(f"Failed to fetch URL {url}: {str(e)}")
                    continue
            
            if full_text_segments:
                combined_text = "\n".join(full_text_segments)
                email_tokens = estimate_token_count(combined_text)

                if current_batch_tokens + email_tokens > max_tokens_per_batch and batch_texts:
                    # Process current batch
                    process_batch(batch_texts, batch_metadata, user, db)
                    batch_texts, batch_metadata, current_batch_tokens = [], [], 0

                batch_texts.append(combined_text)
                batch_metadata.append({"message_id": msg_id, "paid": detect_paid_status(combined_text)})
                current_batch_tokens += email_tokens

        except Exception as e:
            logger.error(f"Error processing message {msg_id}: {str(e)}")
            logger.error(traceback.format_exc())

    # Process any remaining batch
    if batch_texts:
        process_batch(batch_texts, batch_metadata, user, db)

    db.close()
    return "Sync completed"

def process_batch(batch_texts, batch_metadata, user, db):
    try:
        logger.info(f"Sending batch of {len(batch_texts)} emails to OpenAI for analysis")
        bill_data_batch = extract_bills_data_from_batch(batch_texts)

        for bill_data, metadata in zip(bill_data_batch, batch_metadata):
            try:
                bill = models.Bill(
                    user_id=user.id,
                    message_id=metadata["message_id"],
                    vendor=bill_data.get("vendor"),
                    date=bill_data.get("date"),
                    due_date=bill_data.get("due_date"),
                    amount=bill_data.get("amount"),
                    currency=bill_data.get("currency"),
                    category=bill_data.get("category"),
                    status=bill_data.get("status"),
                    blob_name="",
                    paid=metadata["paid"]
                )
                db.add(bill)
                db.commit()
            except Exception as e:
                logger.error(f"Error saving bill to database: {str(e)}")
                db.rollback()

    except Exception as e:
        logger.error(f"Batch processing failed: {str(e)}")
        logger.error(traceback.format_exc())

def detect_paid_status(bill_text: str) -> bool:
    paid_keywords = ["receipt", "payment confirmation", "קבלה", "אישור תשלום"]
    return any(keyword.lower() in bill_text.lower() for keyword in paid_keywords)
