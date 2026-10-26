import os
import re
import subprocess
from pathlib import Path
from rapidocr_onnxruntime import RapidOCR
from src.config import SCREEN_FILE

class OCREngine:
    def __init__(self):
        self.ocr = RapidOCR()

    @staticmethod
    def check_adb_device():
        """
        Kiểm tra xem có thiết bị Android nào đang kết nối qua ADB không
        """
        try:
            res = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=5)
            lines = res.stdout.strip().split("\n")[1:]
            devices = [l.split("\t")[0] for l in lines if "\tdevice" in l]
            return devices
        except Exception:
            return []

    @staticmethod
    def capture_screen():
        """
        Chụp ảnh màn hình điện thoại qua ADB và lưu vào SCREEN_FILE
        """
        if SCREEN_FILE.exists():
            try:
                os.remove(SCREEN_FILE)
            except Exception:
                pass

        try:
            subprocess.run(["adb", "shell", "screencap", "-p", "/sdcard/screen.png"], 
                           capture_output=True, timeout=5)
            subprocess.run(["adb", "pull", "/sdcard/screen.png", str(SCREEN_FILE)], 
                           capture_output=True, timeout=5)
            return SCREEN_FILE.exists() and SCREEN_FILE.stat().st_size > 0
        except Exception:
            return False

    def recognize(self):
        """
        Chạy nhận diện chữ OCR trên ảnh chụp màn hình
        """
        if not SCREEN_FILE.exists():
            return None
        result, _ = self.ocr(str(SCREEN_FILE))
        return result

    @staticmethod
    def parse_screen(ocr_items):
        """
        Tách số câu hỏi, nội dung câu hỏi và các lựa chọn đáp án từ kết quả OCR
        """
        if not ocr_items:
            return None, "", []

        q_num = None
        q_lines = []
        opt_lines = []

        in_q = False
        in_opts = False

        for item in ocr_items:
            text = item[1].strip()
            y = int(item[0][0][1])

            # Bỏ qua status bar và header trên cùng
            if y < 350 and any(k in text.lower() for k in ['kb/s', 'kiem tra', 'danh gia', 'nop bai', '00:']):
                continue
            # Bỏ qua nút dưới cùng
            if y > 2100 or 'danh sach' in text.lower():
                continue

            m = re.match(r'^(Cau|Câu)\s*(\d+)[:\.]?\s*(.*)', text, re.I)
            if m:
                in_q = True
                q_num = m.group(2)
                first_q_text = m.group(3).strip()
                if first_q_text:
                    q_lines.append(first_q_text)
                continue

            if in_q and not in_opts:
                q_lines.append(text)
                if '?' in text or len(q_lines) >= 4:
                    in_opts = True
            elif in_opts:
                opt_lines.append(text)

        # Nếu dòng đầu tiên trong options có dấu hỏi '?' hoặc từ nghi vấn, gộp về q_lines
        while opt_lines and ('?' in opt_lines[0] or any(opt_lines[0].lower().endswith(w) for w in ['gi?', 'nao?', 'the nao?', 'bao nhieu?'])):
            q_lines.append(opt_lines.pop(0))

        return q_num, " ".join(q_lines).strip(), opt_lines
