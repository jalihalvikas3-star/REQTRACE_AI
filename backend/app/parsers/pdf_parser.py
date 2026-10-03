import pymupdf


def extract_pdf_text(file_path):
    text = ""

    pdf = pymupdf.open(file_path)

    for page in pdf:
        text += page.get_text()

    pdf.close()

    return text