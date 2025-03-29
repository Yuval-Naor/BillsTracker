from openai import AzureOpenAI
import json
from app.config import settings
from loguru import logger
import time
import re
from typing import List, Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Handle different OpenAI package structures across versions
try:
    # For newer OpenAI versions (1.0+)
    from openai.types.error import APIError, RateLimitError
    from openai.types import OpenAIError
except ImportError:
    # Fallback for older versions or different structure
    try:
        from openai import APIError, RateLimitError, OpenAIError
    except ImportError:
        # Define custom error classes if imports fail
        class OpenAIError(Exception):
            """Base class for OpenAI errors"""
            pass
            
        class APIError(OpenAIError):
            """Error raised when API request fails"""
            pass
            
        class RateLimitError(OpenAIError):
            """Error raised when rate limit is hit"""
            pass

client = AzureOpenAI(
    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
    api_key=settings.AZURE_OPENAI_KEY,
    api_version=settings.AZURE_OPENAI_API_VERSION
)

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((RateLimitError, APIError)),
    reraise=True
)
def call_openai_with_retry(*args, **kwargs):
    """
    Wrapper for OpenAI API calls with retry logic.
    Retries on RateLimitError and APIError with exponential backoff.
    """
    try:
        response = client.chat.completions.create(*args, **kwargs)
        return response
    except RateLimitError as e:
        logger.warning(f"Rate limit hit: {e}. Retrying...")
        raise
    except APIError as e:
        logger.warning(f"API error: {e}. Retrying...")
        raise

def preprocess_raw_text(text: str) -> str:
    """
    Minimally clean raw text from various sources (email, PDF, OCR) 
    to prepare it for the LLM without losing important information.
    """
    if not text:
        return ""
    
    # Replace excessive newlines with a single newline
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove common OCR artifacts and non-printable characters
    text = re.sub(r'[^\x20-\x7E\u0590-\u05FF\u200e\u200f\s\n.,;:!?()[\]{}\"\'`~@#$%^&*+=<>|/\\-]', ' ', text)
    
    # Normalize spaces
    text = re.sub(r'\s{2,}', ' ', text)
    
    return text.strip()

def extract_bill_data(bill_text: str) -> dict:
    """Extract data from a single bill text"""
    # Clean up the text but don't parse it
    processed_text = preprocess_raw_text(bill_text)
    
    system_prompt = """
You are an AI specialized in bill and invoice information extraction. Your task is to extract structured data from bill text in any language (especially supporting both English and Hebrew).

IMPORTANT INSTRUCTIONS:
- Do NOT translate any text - keep vendor names and other fields in their original language
- For Hebrew text, respect RTL formatting and Hebrew date formats
- Extract numeric values only for amount fields (no currency symbols)
- If information is not found, use null (not empty string or placeholder text)
- Be precise, focusing only on actual bill information (not email signatures, headers, etc.)

You must extract these fields:
- vendor: The company or person issuing the bill
- date: The issue date of the bill (in original format)
- due_date: The payment due date (in original format)
- amount: ONLY the numeric value (e.g., 100.50)
- currency: The currency code or symbol (e.g., USD, NIS, ₪, $)
- category: The bill category (e.g., utilities, rent, insurance, etc.)
- status: Payment status (e.g., paid, unpaid, due)

EXAMPLES:

Example 1 (English):
```
Invoice from ABC Corp
Date: 2023-01-01
Due Date: 2023-01-15
Amount: $100.50
Currency: USD
Category: Utilities
Status: Unpaid
```

Example 2 (Hebrew):
```
חשבונית מחברת XYZ
תאריך: 01/01/2023
תאריך לתשלום: 15/01/2023
סכום: ₪200.75
מטבע: NIS
קטגוריה: שכירות
סטטוס: שולם
```
"""
    user_prompt = f"""Invoice Text:\n{processed_text}\nExtract the data as JSON."""
    try:
        response = call_openai_with_retry(
            model=settings.AZURE_OPENAI_ENGINE,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0,
            max_tokens=500,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        
        logger.debug(f"OpenAI raw response: {content[:100]}...")
        
        if not content or not content.strip():
            logger.error("OpenAI returned empty content")
            return {}
            
        try:
            data = json.loads(content.strip())
            return validate_and_clean_bill_data(data)
        except json.JSONDecodeError as json_err:
            logger.warning(f"JSON parsing failed: {json_err}. Attempting to extract JSON manually.")
            
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group(0))
                    return validate_and_clean_bill_data(data)
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse extracted JSON-like content")
            
            logger.error(f"Failed to parse any JSON from content: {content[:200]}...")
            return {}
            
    except RateLimitError as e:
        logger.error(f"Rate limit exceeded: {e}")
        return {}
    except APIError as e:
        logger.error(f"API error occurred: {e}")
        return {}
    except Exception as e:
        logger.error(f"OpenAI extraction error: {e}")
        return {}

def extract_multiple_bills_data(bill_texts: List[str], batch_size: int = 5) -> List[Dict]:
    """Process multiple bills in batches to reduce API calls"""
    results = []
    batches = [bill_texts[i:i + batch_size] for i in range(0, len(bill_texts), batch_size)]
    
    for batch_index, batch in enumerate(batches):
        logger.info(f"Processing batch {batch_index + 1}/{len(batches)} with {len(batch)} bills")
        
        try:
            batch_results = _process_bill_batch(batch)
            results.extend(batch_results)
            
            if batch_index < len(batches) - 1:
                time.sleep(1)
                
        except Exception as e:
            logger.error(f"Error processing batch {batch_index + 1}: {e}")
            for bill_text in batch:
                try:
                    single_result = extract_bill_data(bill_text)
                    if single_result:
                        results.append(single_result)
                    time.sleep(0.5)
                except Exception as e:
                    logger.error(f"Failed to process individual bill: {str(e)[:100]}...")
    
    return results

def _process_bill_batch(bill_texts: List[str], max_retries: int = 3) -> List[Dict]:
    """Process a batch of bills with a single API call"""
    if not bill_texts:
        return []
    
    system_prompt = """
You are an AI specialized in bill and invoice information extraction. Your task is to extract structured data from bill text in any language (especially supporting both English and Hebrew).

IMPORTANT INSTRUCTIONS:
- Do NOT translate any text - keep vendor names and other fields in their original language
- For Hebrew text, respect RTL formatting and Hebrew date formats
- Extract numeric values only for amount fields (no currency symbols)
- If information is not found, use null (not empty string or placeholder text)
- Be precise, focusing only on actual bill information (not email signatures, headers, etc.)

You must extract these fields:
- vendor: The company or person issuing the bill
- date: The issue date of the bill (in original format)
- due_date: The payment due date (in original format)
- amount: ONLY the numeric value (e.g., 100.50)
- currency: The currency code or symbol (e.g., USD, NIS, ₪, $)
- category: The bill category (e.g., utilities, rent, insurance, etc.)
- status: Payment status (e.g., paid, unpaid, due)

EXAMPLES:

Example 1 (English):
```
Invoice from ABC Corp
Date: 2023-01-01
Due Date: 2023-01-15
Amount: $100.50
Currency: USD
Category: Utilities
Status: Unpaid
```

Example 2 (Hebrew):
```
חשבונית מחברת XYZ
תאריך: 01/01/2023
תאריך לתשלום: 15/01/2023
סכום: ₪200.75
מטבע: NIS
קטגוריה: שכירות
סטטוס: שולם
```
"""
    
    formatted_texts = "\n\n---INVOICE SEPARATOR---\n\n".join([f"INVOICE {i+1}:\n{text}" for i, text in enumerate(bill_texts)])
    user_prompt = f"""Multiple Invoice Texts:\n{formatted_texts}\n\nExtract each invoice's data as a JSON array of objects."""
    
    retries = 0
    while retries <= max_retries:
        try:
            response = call_openai_with_retry(
                model=settings.AZURE_OPENAI_ENGINE,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.0,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            logger.debug(f"Batch processing raw response: {content[:100]}...")
            
            try:
                data = json.loads(content.strip())
                if isinstance(data, dict) and "invoices" in data:
                    bills_data = data["invoices"]
                elif isinstance(data, list):
                    bills_data = data
                else:
                    logger.warning(f"Unexpected response structure: {type(data)}")
                    bills_data = [data]
                return [validate_and_clean_bill_data(bill) for bill in bills_data]
            except json.JSONDecodeError:
                logger.error(f"Failed to parse batch response JSON: {content[:200]}...")
                break
        except RateLimitError as e:
            logger.warning(f"Rate limit error on batch (try {retries+1}/{max_retries+1}): {e}")
            retries += 1
            if retries <= max_retries:
                sleep_time = 2 ** retries
                logger.info(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                logger.error(f"Failed to process batch after {max_retries} retries")
                break
        except APIError as e:
            logger.warning(f"API error on batch (try {retries+1}/{max_retries+1}): {e}")
            retries += 1
        except Exception as e:
            logger.error(f"Unexpected error during batch processing: {e}")
            break
    return []

def validate_and_clean_bill_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and clean bill data to prevent DB errors"""
    clean_data = {}
    for field in ["vendor", "date", "due_date", "amount", "currency", "category", "status"]:
        value = data.get(field)
        if field == "amount":
            if value is None or value == "":
                clean_data[field] = None
            else:
                try:
                    import re
                    numeric_str = re.sub(r'[^\d.]', '', str(value))
                    if numeric_str:
                        clean_data[field] = float(numeric_str)
                    else:
                        clean_data[field] = None
                except (ValueError, TypeError):
                    logger.warning(f"Invalid amount value: {value}, setting to None")
                    clean_data[field] = None
        else:
            if value == "":
                clean_data[field] = None
            else:
                clean_data[field] = value
    return clean_data

def estimate_token_count(text: str) -> int:
    # Simple estimation: 1 token ≈ 0.75 words
    return int(len(text.split()) / 0.75)

def extract_bills_data_from_batch(email_texts: List[str]) -> List[Dict[str, Any]]:
    system_prompt = """
You are an AI specialized in extracting structured bill information from emails. Each email is delimited clearly. Extract structured data separately for each email. Return a JSON array where each element corresponds to one email.

Extract these fields per email:
- vendor
- date
- due_date
- amount (numeric only)
- currency
- category
- status (paid/unpaid/due)

If information is missing, use null.
"""
    formatted_batch = ""
    for idx, email_text in enumerate(email_texts, 1):
        formatted_batch += f"### Email {idx} Start\n{email_text}\n### Email {idx} End\n\n"
    user_prompt = f"Extract structured bill data from each email separately:\n\n{formatted_batch}"
    
    response = call_openai_with_retry(
        model=settings.AZURE_OPENAI_ENGINE,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.0,
        max_tokens=2000,
        response_format={"type": "json_object"}
    )
    content = response.choices[0].message.content
    try:
        data = json.loads(content.strip())
        if isinstance(data, dict) and "emails" in data:
            return [validate_and_clean_bill_data(bill) for bill in data["emails"]]
        elif isinstance(data, list):
            return [validate_and_clean_bill_data(bill) for bill in data]
        else:
            logger.error("Unexpected response structure from OpenAI")
            return [{} for _ in email_texts]
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {str(e)}")
        return [{} for _ in email_texts]
