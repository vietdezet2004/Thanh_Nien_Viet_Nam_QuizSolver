import os
import sys
import time
import winsound
from pathlib import Path

# Thêm thư mục gốc vào sys.path để import src.*
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.config import DOCS_DIR
from src.database import QuizDB
from src.ocr_engine import OCREngine
from src.search_engine import SearchEngine

def print_banner():
    os.system("cls" if os.name == "nt" else "clear")
    print("=" * 68)
    print("     TRỢ LÝ THI THANH NIÊN VIỆT NAM - TỰ ĐỘNG TÌM ĐÁP ÁN CTRL+F")
    print("=" * 68)

def select_documents():
    db = QuizDB()
    all_files = db.available_files

    if not all_files:
        print("\n[!] CẢNH BÁO: Chưa có file tài liệu .md nào trong thư mục 'md_tailieu'!")
        print("    Vui lòng copy các file tài liệu (.md) vào thư mục 'md_tailieu'.")
        input("\nNhấn Enter để thử lại...")
        return select_documents()

    print("\nChọn tài liệu bạn muốn sử dụng để tìm kiếm:\n")
    print("  [0] Tự động tìm kiếm trong TẤT CẢ các file tài liệu (Khuyên dùng)")
    for idx, fname in enumerate(all_files, start=1):
        print(f"  [{idx}] {fname}")
    print("-" * 68)

    choice = input(f"Nhập số (0 - {len(all_files)}) rồi nhấn Enter [Mặc định: 0]: ").strip()
    
    selected_file = None
    if choice.isdigit() and 1 <= int(choice) <= len(all_files):
        selected_file = all_files[int(choice) - 1]

    total_q, total_f = db.load_all(selected_file)
    print(f"\n[OK] Đã nạp thành công {total_q} câu hỏi từ {total_f} file tài liệu.")
    return db, selected_file

def wait_for_adb():
    """Kiểm tra và chờ thiết bị Android kết nối ADB"""
    devices = OCREngine.check_adb_device()
    if devices:
        return devices[0]

    print("\n" + "!" * 68)
    print("  [!] CHƯA PHÁT HIỆN ĐIỆN THOẠI KẾT NỐI ADB!")
    print("  1. Cắm cáp USB nối điện thoại với máy tính.")
    print("  2. Bật 'Tùy chọn cho nhà phát triển' -> Bật 'Gỡ lỗi USB' (USB Debugging).")
    print("  3. Nếu màn hình điện thoại hiện 'Cho phép gỡ lỗi USB?', hãy tích chọn 'Luôn cho phép' và ấn OK.")
    print("  (Xem hướng dẫn chi tiết từng bước trong file README.md)")
    print("!" * 68)
    print("\nĐang tự động quét tìm thiết bị, vui lòng cắm dây...")

    while True:
        devices = OCREngine.check_adb_device()
        if devices:
            print(f"\n[OK] Đã kết nối thành công với thiết bị: {devices[0]}")
            time.sleep(1)
            return devices[0]
        time.sleep(1.5)

def main():
    print_banner()
    db, selected_file = select_documents()

    print("\n[...] Đang kiểm tra kết nối điện thoại qua ADB...")
    device_id = wait_for_adb()

    print("\n[...] Đang khởi tạo mô hình nhận diện chữ OCR (RapidOCR)...")
    ocr_engine = OCREngine()
    searcher = SearchEngine(db)

    last_sig = ""

    os.system("cls" if os.name == "nt" else "clear")
    print("=" * 68)
    target_name = selected_file if selected_file else "TẤT CẢ TÀI LIỆU TRONG md_tailieu"
    print(f"  TRỢ LÝ ĐANG HOẠT ĐỘNG: [{target_name}]")
    print("  Màn hình sẽ TỰ ĐỘNG CẬP NHẬT ĐÁP ÁN ngay khi bạn chuyển câu mới!")
    print("=" * 68 + "\n")

    while True:
        try:
            # 1. Chụp màn hình qua ADB
            if not OCREngine.capture_screen():
                time.sleep(0.4)
                continue

            # 2. Nhận diện chữ OCR
            ocr_result = ocr_engine.recognize()
            if not ocr_result:
                time.sleep(0.4)
                continue

            # 3. Phân tách câu hỏi và các lựa chọn
            q_num, screen_q, screen_opts = OCREngine.parse_screen(ocr_result)
            if not screen_q and not q_num:
                time.sleep(0.4)
                continue

            # 4. Kiểm tra xem đã sang câu hỏi mới chưa
            current_sig = f"{q_num}_{screen_q[:35]}"
            if current_sig == last_sig:
                time.sleep(0.4)
                continue

            last_sig = current_sig

            # 5. Tìm kiếm câu hỏi trong DB theo Ctrl+F
            res = searcher.search(screen_q, screen_opts)

            # Bíp âm thanh báo hiệu
            try:
                winsound.Beep(1200, 120)
            except Exception:
                pass

            # 6. Hiển thị kết quả ra console
            os.system("cls" if os.name == "nt" else "clear")
            print("=" * 68)
            q_label = f"CÂU {q_num}" if q_num else "CÂU HỎI MỚI"
            if res.matched:
                matched_q = res.question
                print(f"[{q_label}] | Nguồn: [{matched_q['file']}]")
                detail_str = f"Câu hỏi khớp {res.q_similarity}%"
                if res.ans_matched:
                    detail_str += " + Trùng khớp phương án trên màn hình"
                print(f"📊 ĐỘ TƯƠNG ĐỒNG: {res.score}%  ({detail_str})")
                print("=" * 68)
                print(f"\nNỘI DUNG CÂU HỎI NHẬN DIỆN ĐƯỢC:\n  {screen_q}\n")
                print("*" * 68)
                print(">>> ĐÁP ÁN ĐÚNG CẦN CHỌN:")
                print(f"\n    👉👉👉  {matched_q['ans_text']}  👈👈👈\n")
                print("*" * 68)
            else:
                print(f"[{q_label}] | ⚠️ CHƯA CÓ TRONG TÀI LIỆU (CÂU HỎI MỚI)")
                if res.closest_q:
                    print(f"📊 ĐỘ TƯƠNG ĐỒNG CÂU GẦN NHẤT: {res.closest_similarity}% (Dưới ngưỡng tin cậy)")
                print("=" * 68)
                print(f"\nNỘI DUNG CÂU HỎI NHẬN DIỆN:\n  {screen_q}\n")
                print("CÁC PHƯƠNG ÁN TRÊN MÀN HÌNH:")
                for opt in screen_opts:
                    print(f"  - {opt}")
                print("\n" + "=" * 68)

            print("\n(Khi bạn chọn xong và ấn 'Tiếp tục', màn hình sẽ tự động đổi)")
            time.sleep(0.5)

        except KeyboardInterrupt:
            print("\n\nĐã dừng trợ lý. Hẹn gặp lại!")
            break
        except Exception as e:
            # Nếu xảy ra lỗi nhỏ (như ADB bận tạm thời), ngủ một nhịp và thử lại
            time.sleep(0.5)

if __name__ == "__main__":
    main()
