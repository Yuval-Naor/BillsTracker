from bs4 import BeautifulSoup

def extract_text_from_html(html_content: str) -> str:
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        return soup.get_text(separator="\n")
    except Exception as e:
        print("HTML extraction error:", e)
        return ""
