import pdfplumber
import pandas as pd
import io

def parse_pdf(file):
    """
    Parses a PDF file and extracts text.
    
    Args:
        file: A file-like object (uploaded file).
        
    Returns:
        str: Extracted text from the PDF.
    """
    text = ""
    try:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        return f"Error parsing PDF: {e}"
    
    return text
