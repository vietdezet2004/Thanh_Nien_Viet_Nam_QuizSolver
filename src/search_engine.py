import difflib
from src.database import normalize_text

class MatchResult:
    def __init__(self, matched=False, question=None, score=0.0, q_similarity=0.0, ans_matched=False, closest_q=None, closest_similarity=0.0):
        self.matched = matched
        self.question = question
        self.score = min(100, int(score * 100))
        self.q_similarity = min(100, int(q_similarity * 100))
        self.ans_matched = ans_matched
        self.closest_q = closest_q
        self.closest_similarity = min(100, int(closest_similarity * 100))

class SearchEngine:
    def __init__(self, db):
        self.db = db

    def search(self, screen_q_text, screen_options):
        """
        Tìm kiếm trực tiếp theo phong cách Ctrl+F:
        1. So khớp nội dung câu hỏi
        2. Đối chiếu chéo đáp án trong DB với các lựa chọn trên màn hình
        """
        q_norm = normalize_text(screen_q_text)
        if not q_norm:
            return MatchResult(matched=False)

        q_words = set(q_norm.split())
        opts_norm = [normalize_text(o) for o in screen_options]

        best_q = None
        best_score = 0.0
        best_q_sim = 0.0
        best_ans_matched = False

        closest_q = None
        closest_sim = 0.0

        for q in self.db.questions:
            db_words = set(q["q_norm"].split())
            if not db_words:
                continue

            # 1. Đo lường độ tương đồng văn bản câu hỏi
            seq_ratio = difflib.SequenceMatcher(None, q_norm, q["q_norm"]).ratio()
            common_words = q_words.intersection(db_words)
            jaccard = len(common_words) / len(q_words.union(db_words))
            q_sim = (seq_ratio * 0.7) + (jaccard * 0.3)

            if q_sim > closest_sim:
                closest_sim = q_sim
                closest_q = q

            # 2. Kiểm tra xem đáp án trong DB có xuất hiện trong các phương án trên màn hình không
            ans_matched = False
            for opt_n in opts_norm:
                if not opt_n:
                    continue
                if opt_n in q["ans_norm"] or q["ans_norm"] in opt_n:
                    ans_matched = True
                    break
                if difflib.SequenceMatcher(None, opt_n, q["ans_norm"]).ratio() > 0.70:
                    ans_matched = True
                    break

            # 3. Tính điểm độ tương đồng tổng hợp
            if ans_matched and (seq_ratio > 0.40 or jaccard > 0.30):
                # Khớp cả câu hỏi và trùng một phương án trên màn hình
                score = 0.60 + (seq_ratio * 0.25) + (jaccard * 0.15)
                if score > best_score:
                    best_score = score
                    best_q = q
                    best_q_sim = q_sim
                    best_ans_matched = True
            elif not ans_matched and (seq_ratio > 0.75 or jaccard > 0.60):
                # Câu hỏi khớp rất cao dù OCR phương án có thể bị mờ/thiếu
                score = q_sim
                if score > best_score:
                    best_score = score
                    best_q = q
                    best_q_sim = q_sim
                    best_ans_matched = False

        if best_q and best_score >= 0.50:
            return MatchResult(
                matched=True,
                question=best_q,
                score=best_score,
                q_similarity=best_q_sim,
                ans_matched=best_ans_matched
            )

        return MatchResult(
            matched=False,
            closest_q=closest_q,
            closest_similarity=closest_sim
        )
