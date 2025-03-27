import openai, json
from app.config import settings

openai.api_type = "azure"
openai.api_base = settings.AZURE_OPENAI_ENDPOINT
openai.api_key = settings.AZURE_OPENAI_KEY
openai.api_version = settings.AZURE_OPENAI_API_VERSION

def extract_bill_data(bill_text: str) -> dict:
    system_prompt = (
        "You are an assistant that extracts structured invoice information. "
        "The input invoice may be in English or Hebrew. Do not translate any text; output the data in the original language. "
        "Extract the following fields: vendor, date, due_date, amount, currency, category, status. "
        "Output only a JSON object with these keys."
    )
    user_prompt = f"Invoice Text:\n"""\n{bill_text}\n"""\nExtract the data as JSON."
    try:
        response = openai.ChatCompletion.create(
            engine=settings.AZURE_OPENAI_ENGINE,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0,
            max_tokens=500
        )
        content = response['choices'][0]['message']['content']
        data = json.loads(content.strip())
        return data
    except Exception as e:
        print("OpenAI extraction error:", e)
        return {}
