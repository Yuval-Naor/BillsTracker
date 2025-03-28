from openai import AzureOpenAI
import json
from app.config import settings
from loguru import logger

# Initialize Azure OpenAI client
client = AzureOpenAI(
    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
    api_key=settings.AZURE_OPENAI_KEY,
    api_version=settings.AZURE_OPENAI_API_VERSION
)

def extract_bill_data(bill_text: str) -> dict:
    system_prompt = (
        "You are an assistant that extracts structured invoice information. "
        "The input invoice may be in English or Hebrew. Do not translate any text; output the data in the original language. "
        "Extract the following fields: vendor, date, due_date, amount, currency, category, status. "
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
            max_tokens=500
        )
        # New response structure
        content = response.choices[0].message.content
        data = json.loads(content.strip())
        return data
    except Exception as e:
        logger.error(f"OpenAI extraction error: {e}")
        return {}
