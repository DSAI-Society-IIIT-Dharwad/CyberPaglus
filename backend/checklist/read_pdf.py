import sys
import subprocess

try:
    import PyPDF2
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "PyPDF2"])
    import PyPDF2

def read_pdf(file_path, out_path):
    with open(file_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
    with open(out_path, "w", encoding="utf-8") as out_f:
        out_f.write(text)

read_pdf(
    r"c:\Users\akars\OneDrive\Desktop\kuber attack path visualizer\backend\checklist\scoring-rubric.pdf",
    r"c:\Users\akars\OneDrive\Desktop\kuber attack path visualizer\backend\checklist\rubric.txt"
)
