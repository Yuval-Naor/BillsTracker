"""
Debug script for Gmail API permissions.
Run this script to verify Gmail API connectivity and permissions.
"""

import os
import sys
import requests
from loguru import logger

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import User
from app.services.gmail_service import refresh_access_token

def check_gmail_api_permissions():
    """
    Test Gmail API access with stored credentials
    """
    logger.info("Starting Gmail API diagnostic tool")
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Get all users
        users = db.query(User).all()
        if not users:
            logger.error("No users found in database")
            return
            
        for user in users:
            logger.info(f"Testing Gmail API for user: {user.email} (ID: {user.id})")
            
            # Check if refresh token exists
            if not user.google_refresh_token:
                logger.error(f"No refresh token stored for user {user.email}")
                continue
                
            try:
                # Try to refresh the token
                logger.info("Attempting to refresh access token...")
                access_token = refresh_access_token(user.google_refresh_token)
                logger.success("Successfully refreshed access token")
                
                # Test basic Gmail API call
                logger.info("Testing Gmail API access with basic metadata request...")
                url = "https://gmail.googleapis.com/gmail/v1/users/me/profile"
                headers = {"Authorization": f"Bearer {access_token}"}
                resp = requests.get(url, headers=headers)
                
                if resp.ok:
                    profile = resp.json()
                    logger.success(f"Gmail API access successful - Email: {profile.get('emailAddress')}")
                    logger.info(f"Gmail account has {profile.get('messagesTotal', '?')} total messages")
                else:
                    logger.error(f"Gmail API access failed: {resp.status_code} - {resp.text}")
            
                # Test query that's failing in application
                logger.info("Testing problematic query...")
                query = 'has:attachment OR subject:(bill OR invoice OR חשבונית OR קבלה)'
                url = "https://gmail.googleapis.com/gmail/v1/users/me/messages"
                params = {"q": query, "maxResults": 5}
                resp = requests.get(url, params=params, headers=headers)
                
                if resp.ok:
                    data = resp.json()
                    messages = data.get("messages", [])
                    logger.success(f"Query successful! Found {len(messages)} messages")
                else:
                    logger.error(f"Query failed with status {resp.status_code}")
                    logger.error(f"Response: {resp.text}")
                    
            except Exception as e:
                logger.exception(f"Error testing Gmail API for {user.email}: {str(e)}")
                
    finally:
        db.close()
        
    logger.info("Gmail API diagnostic completed")

if __name__ == "__main__":
    check_gmail_api_permissions()
