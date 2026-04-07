import sys
import subprocess

try:
    import PyPDF2
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "PyPDF2"])
    import PyPDF2

try:
    reader = PyPDF2.PdfReader('B600_TA_01_SAMUEL P._Revisi 2 -_.pdf')
    text = ""
    for page in reader.pages:
        text += page.extract_text()

    with open('pdf_text.txt', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Success")
except Exception as e:
    print(f"Error: {e}")
