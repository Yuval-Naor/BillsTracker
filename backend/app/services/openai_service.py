from openai import AzureOpenAI
import json
from app.config import settings
from loguru import logger
import time
from typing import List, Dict, Any, Optional

# Initialize Azure OpenAI client
client = AzureOpenAI(
    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
    api_key=settings.AZURE_OPENAI_KEY,
    api_version=settings.AZURE_OPENAI_API_VERSION
)

def extract_bill_data(bill_text: str) -> dict:
    """Extract data from a single bill text (legacy method)"""
    system_prompt = (
        "You are an assistant that extracts structured invoice information. "
        "The input invoice may be in English or Hebrew. Do not translate any text; output the data in the original language. "
        "For Hebrew text, ensure correct handling of RTL formatting and Hebrew date formats. "
        "Extract the following fields: vendor, date, due_date, amount, currency, category, status. "
        "For amount, extract only the numeric value. If a field is not found, return null instead of an empty string. "
        "Output only a JSON object with these keys."
    )
    user_prompt = f"""Invoice Text:\n{bill_text}\nExtract the data as JSON."""
    try:
        # New API call format for OpenAI >= 1.0.0
        response = client.chat.completions.create(
            model=settings.AZURE_OPENAI_ENGINE,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0,
            max_tokens=500,
            response_format={"type": "json_object"}  # Explicitly request JSON format
        )
        # New response structure
        content = response.choices[0].message.content
        
        # Log the raw content for debugging
        logger.debug(f"OpenAI raw response: {content[:100]}...")
        
        if not content or not content.strip():
            logger.error("OpenAI returned empty content")
            return {}
            
        try:
            data = json.loads(content.strip())
            # Validate and clean up data
            return validate_and_clean_bill_data(data)
        except json.JSONDecodeError as json_err:
            # If JSON parsing fails, try to extract JSON-like content using a simple heuristic
            logger.warning(f"JSON parsing failed: {json_err}. Attempting to extract JSON manually.")
            
            # Try to find content between curly braces
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group(0))
                    return validate_and_clean_bill_data(data)
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse extracted JSON-like content")
            
            # Return empty dict if all parsing attempts fail
            logger.error(f"Failed to parse any JSON from content: {content[:200]}...")
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
            
            # Add small delay between batches to avoid rate limiting
            if batch_index < len(batches) - 1:
                time.sleep(1)
                
        except Exception as e:
            logger.error(f"Error processing batch {batch_index + 1}: {e}")
            # If a batch fails, try processing each bill individually
            for bill_text in batch:
                try:
                    single_result = extract_bill_data(bill_text)
                    if single_result:
                        results.append(single_result)
                    # Small delay to avoid rate limits
                    time.sleep(0.5)
                except Exception as e:
                    logger.error(f"Failed to process individual bill: {str(e)[:100]}...")
    
    return results

def _process_bill_batch(bill_texts: List[str], max_retries: int = 3) -> List[Dict]:
    """Process a batch of bills with a single API call"""
    if not bill_texts:
        return []
    
    # Construct a system prompt with better Hebrew support
    system_prompt = (
        "You are an assistant that extracts structured invoice information from multiple invoices. "
        "The input invoices may be in English or Hebrew. Do not translate any text; output the data in the original language. "
        "For Hebrew text, ensure correct handling of RTL formatting and Hebrew date formats. "
        "For each invoice, extract: vendor, date, due_date, amount, currency, category, status. "
        "For amount, extract only the numeric value without currency symbols. "
        "If a field is not found, use null instead of an empty string. "
        "Output a JSON array where each object represents one invoice."
    )
    
    # Format the bill texts with separator
    formatted_texts = "\n\n---INVOICE SEPARATOR---\n\n".join([f"INVOICE {i+1}:\n{text}" for i, text in enumerate(bill_texts)])
    user_prompt = f"""Multiple Invoice Texts:\n{formatted_texts}\n\nExtract each invoice's data as a JSON array of objects."""
    
    retries = 0
    while retries <= max_retries:
        try:
            response = client.chat.completions.create(
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
            
            # Parse the response - expecting a JSON array
            try:
                data = json.loads(content.strip())
                if isinstance(data, dict) and "invoices" in data:
                    # Handle case where response is {invoices: [...]}
                    bills_data = data["invoices"]
                elif isinstance(data, list):
                    # Handle case where response is directly an array
                    bills_data = data
                else:
                    # Handle case where response is some other structure
                    logger.warning(f"Unexpected response structure: {type(data)}")
                    bills_data = [data]  # Treat as single bill
                
                # Validate each bill
                return [validate_and_clean_bill_data(bill) for bill in bills_data]
                
            except json.JSONDecodeError:
                logger.error(f"Failed to parse batch response JSON: {content[:200]}...")
                break
                
        except Exception as e:
            logger.warning(f"Batch processing error (try {retries+1}/{max_retries+1}): {e}")
            retries += 1
            # Exponential backoff for retries
            if retries <= max_retries:
                sleep_time = 2 ** retries
                logger.info(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                logger.error(f"Failed to process batch after {max_retries} retries")
                break
    
    # If we get here, batch processing failed - return empty list
    return []

def validate_and_clean_bill_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and clean bill data to prevent DB errors"""
    clean_data = {}
    
    # Ensure these fields are dictionary keys
    for field in ["vendor", "date", "due_date", "amount", "currency", "category", "status"]:
        # Get value or None if not present
        value = data.get(field)
        
        # Special handling for amount field to ensure it's None or a valid float
        if field == "amount":
            if value is None or value == "":
                clean_data[field] = None
            else:
                try:
                    # Try to convert to float, handling strings like "100.00"
                    # Remove any non-numeric chars except decimal point
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
            # For non-amount fields, convert empty strings to None
            if value == "":
                clean_data[field] = None
            else:
                clean_data[field] = value
    
    return clean_data
