import os
import sys
from pathlib import Path

# Thư mục gốc dự án
BASE_DIR = Path(__file__).resolve().parent.parent

# Thư mục tài liệu chứa các file .md
DOCS_DIR = BASE_DIR / "md_tailieu"

# Tệp ảnh chụp màn hình tạm thời
SCREEN_FILE = BASE_DIR / "screen.png"

# Đảm bảo UTF-8 cho Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass
