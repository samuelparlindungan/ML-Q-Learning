import sys
import subprocess
import os

def install_pkg(pkg):
    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

try:
    import PyPDF2
except ImportError:
    install_pkg("PyPDF2")
    import PyPDF2

try:
    import docx
except ImportError:
    install_pkg("python-docx")
    import docx

def read_pdf(file_path):
    text = ""
    try:
        reader = PyPDF2.PdfReader(file_path)
        for page in reader.pages:
            t = page.extract_text()
            if t: text += t + "\n"
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    return text

def read_docx(file_path):
    text = ""
    try:
        doc = docx.Document(file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    return text

files = [
    "B100_TA_01_Revisi 3.docx",
    "B200_TA_01._Revisi 2.docx",
    "B600 Josh Delon Revisi_2.pdf",
    "B600_TA_01_SAMUEL P._Revisi 2 -_.pdf"
]

with open('summary_all.txt', 'w', encoding='utf-8') as out:
    for f in files:
        out.write(f"\n{'='*40}\nFILE: {f}\n{'='*40}\n")
        if f.endswith('.pdf'):
            text = read_pdf(f)
        elif f.endswith('.docx'):
            text = read_docx(f)
        
        # Summary approach: print only first 10000 chars of each to get context (like abstract, chapter 1 & 2)
        out.write(text[:15000]) # First 15k chars is enough for scope context

print("Extraction complete.")
