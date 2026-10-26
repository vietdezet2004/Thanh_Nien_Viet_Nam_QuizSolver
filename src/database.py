import os
import re
import glob
import unicodedata
from pathlib import Path
from src.config import DOCS_DIR

def strip_accents(s):
    if not s:
        return ""
    s = unicodedata.normalize('NFD', s)
    s = "".join(c for c in s if unicodedata.category(c) != 'Mn')
    return s.replace('đ', 'd').replace('Đ', 'D')

def normalize_text(s):
    if not s:
        return ""
    s = strip_accents(s).lower()
    s = re.sub(r'[\r\n\t]+', ' ', s)
    s = re.sub(r'[^a-z0-9\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

class QuizDB:
    def __init__(self, target_file=None):
        self.questions = []
        self.available_files = []
        self.load_all(target_file)

    def scan_files(self):
        if not DOCS_DIR.exists():
            DOCS_DIR.mkdir(parents=True, exist_ok=True)
        return sorted([f for f in DOCS_DIR.glob("*.md")])

    def load_all(self, target_file=None):
        self.questions = []
        all_files = self.scan_files()
        self.available_files = [f.name for f in all_files]

        if target_file:
            files_to_load = [f for f in all_files if f.name.lower() == target_file.lower()]
        else:
            files_to_load = all_files

        for fpath in files_to_load:
            self.load_file(fpath)

        return len(self.questions), len(files_to_load)

    def load_file(self, fpath):
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            print(f"[-] Không thể đọc file {fpath.name}: {e}")
            return

        raw_blocks = re.split(r'(?=Câu hỏi\s+\d+\.)', content)
        for block in raw_blocks:
            if not block.strip().startswith("Câu hỏi"):
                continue

            q_match = re.search(r'Câu hỏi\s+\d+\.?\s*(.*?)(?=\n[A-D]\.|\nĐáp án:|$)', block, re.DOTALL)
            if not q_match:
                continue
            q_text = q_match.group(1).strip()
            q_text = re.sub(r'^\.\s*', '', q_text)

            options = {}
            for opt in ['A', 'B', 'C', 'D']:
                opt_match = re.search(rf'\n{opt}\.\s*(.*?)(?=\n[A-D]\.|\nĐáp án:|$)', block, re.DOTALL)
                if opt_match:
                    options[opt] = opt_match.group(1).strip()

            ans_match = re.search(r'Đáp án:\s*([A-D])', block)
            if not ans_match:
                continue
            correct_letter = ans_match.group(1)
            correct_text = options.get(correct_letter, "")

            if correct_text:
                self.questions.append({
                    "file": fpath.name,
                    "q_raw": q_text,
                    "q_norm": normalize_text(q_text),
                    "options": options,
                    "ans_letter": correct_letter,
                    "ans_text": correct_text,
                    "ans_norm": normalize_text(correct_text)
                })
