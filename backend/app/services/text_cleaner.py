import re

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    text = text.replace("\n", " ")
    return text.strip()