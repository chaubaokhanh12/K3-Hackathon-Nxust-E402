# AI SPEC — DupBot: Semantic Duplicate Detection Bot for Discord Q&A

Hướng: ☑ B — Trợ lý Học viên
Loại: ☑ Tính năng mới

> Ghi chú điền tên: các ô **[TÊN THÀNH VIÊN x]** trong §8 để nhóm trưởng điền tên
> thật. Không đổi cột "Vai trò" (6 người – 6 role) để giữ đúng phân công.

---

# §1. User & Job

### Job executor + workflow

**Người dùng:** Học viên khoá AI Thực Chiến đặt câu hỏi trên kênh "Hỏi đáp" Discord;
LabCoach/Mentor/Admin là người phản hồi.

**Workflow**

1. Học viên gặp lỗi hoặc thắc mắc trong lúc học/làm dự án.
2. Nhập câu hỏi vào kênh Discord "Hỏi đáp".
3. Bot tự động phân tích ngữ nghĩa câu hỏi (embedding + topic).
4. Bot tìm các thread cũ **cùng vấn đề đã có lời giải** bằng Semantic Search.
5. Bot phân loại độ chắc chắn (HIGH / LOW / NONE) và đề xuất tối đa 3 thread kèm
   link gốc + trích đoạn nguyên văn, hoặc tự chuyển đúng người phụ trách.
6. Học viên đọc lại lời giải cũ, hoặc bấm nút phản hồi để được chuyển tiếp.

### Core JTBD

> Khi gặp một vấn đề trong khoá học, tôi muốn tìm và đối chiếu ngay lập tức giải pháp
> từ các vấn đề tương tự đã được giải quyết trước đó, để không phải chờ đợi câu trả lời
> cho một câu hỏi mà người khác đã từng hỏi.

### Problem Statement

Học viên mất nhiều thời gian chờ phản hồi cho các câu hỏi trùng lặp — những lỗi hoặc
thắc mắc mà người khác đã gặp và đã được giải quyết. Điều này khiến kênh Hỏi đáp lộn
xộn, tăng số câu hỏi lặp, và bắt LabCoach phải trả lời cùng một vấn đề nhiều lần.

### Evidence

- **Số liệu mining (chuẩn B):** 82% thread thuộc về một nhóm trùng lặp (đếm được trên
  corpus, phương pháp kiểm lại được).
- **Khảo sát:** Trung vị thời gian chờ để có câu trả lời **đã xác minh** là **522 phút
  (~9 tiếng)**.
- **≥5 quote/ví dụ nguyên văn:**
  - "phoenix không load được phần đội của tôi"
  - "sửa code trong folder /script có ảnh hưởng chấm điểm không?"
  - "deadline nộp sản phẩm cuối cùng là ngày nào"
  - "diem cong trên lớp có đổi thành xp không"
  - "lỗi font tiếng việt khi export pdf"

---

# §2. Impact & Quyết định chọn

| Ứng viên                               | Ai × Tần suất × Chi phí mỗi lần                              | Mức ảnh hưởng    | Khả thi |
| -------------------------------------- | ------------------------------------------------------------ | ---------------- | ------- |
| **Semantic Search thread cũ (CHỌN)**   | Toàn bộ học viên × tần suất cao × tiết kiệm ~9 tiếng chờ/lần | Cao              | Cao     |
| Tự động sinh câu trả lời mới hoàn toàn | Mọi học viên × cao × rủi ro sai quy định/deadline            | Rất cao (rủi ro) | Thấp    |
| Bản tin cuối ngày cho TA               | Chỉ TA × 1 lần/ngày × không giảm thời gian chờ thật          | Trung bình       | Cao     |

### Ứng viên đã loại

**Tự động sinh câu trả lời mới hoàn toàn** — rủi ro **ảo giác** thông tin quy định /
deadline dẫn đến hậu quả trực tiếp (học viên mất điểm). Chi phí kiểm thử chống sai cao.

**Bản tin cuối ngày cho TA** — chỉ giúp TA, không giải quyết thời gian chờ thực tế của
học viên.

### Ứng viên được chọn

**Semantic Search + phân tầng nguồn thread cũ đã xác minh (HIGH/LOW/NONE)** — giải
quyết trực tiếp thời gian chờ, dựa trên nguồn thực tế đã được xác minh, và dễ đo bằng
Precision@3 / tỷ lệ không-bịa.

---

# §3. Giải pháp tương tự đã nghiên cứu

### Discord Search (gốc)

**Đáng học:** nhanh, có sẵn trên Discord.
**Đáng né:** chỉ so khớp từ khóa, miss khi diễn đạt khác; không phân tầng được nguồn.

### AI Chatbot thông thường

**Đáng học:** trả lời tức thì, hội thoại tự nhiên.
**Đáng né:** hay tự sinh câu trả lời mới (hallucinate), không phân biệt được "biết" và
"không biết".

### Điểm khác biệt

DupBot dùng **Semantic Search** để hiểu ý nghĩa thay vì so khớp từ khóa, **chỉ lấy
snippet nguyên văn** từ thread cũ (không tự sinh), và phân **3 tier confidence** để
trung thực về độ chắc chắn.

---

# §4. Thiết kế

### Lát cắt MỘT CÂU

> Học viên đặt câu hỏi → AI phân loại mức độ tương đồng (HIGH/LOW/NONE) với các thread
> cũ → đề xuất tối đa 3 thread đã giải quyết, hoặc tự động chuyển đúng người phụ trách.

_(1 user · 1 việc · 1 quyết định AI · 1 kết quả — khớp bản build.)_

### Non-goals (≥3)

1. KHÔNG tạo mới / KHÔNG giải thích dài dòng.
2. KHÔNG tự bịa hoặc viết lại câu trả lời (chỉ dùng snippet **verbatim**).
3. KHÔNG trả lời câu hỏi ngoài phạm vi khoá học.

### Prototype

☑ **Working** — backend tool (embedding + retrieval + guardrails) kết nối frontend thật
(giao diện mô phỏng Discord).

**Thành phần thật:** Semantic Search (embedding), phân tầng nguồn, guardrails.
**Mock (ghi rõ):** fallback tìm kiếm cục bộ khi không có `OPENAI_API_KEY`.

### Automation

☑ **Conditional** — có threshold cho HIGH/LOW/NONE.
**Lý do theo cost-of-error:** sai thông tin quy định làm học viên mất điểm → **fail-closed
về NONE** (thà nói "chưa có" còn hơn bịa).

### Nguyên tắc HAX/PAIR (≥4, mỗi nguyên tắc trỏ vào chỗ cụ thể trong prototype)

| Nguyên tắc                        | Áp cụ thể vào đâu trong prototype                                    |
| --------------------------------- | -------------------------------------------------------------------- |
| Match system to real world        | Kết quả trả về dạng**Card** có Confidence, Excerpt, AnsweredBy       |
| Make clear what the system can do | Phân loại rõ**HIGH / LOW / NONE** và nói thẳng "chưa có" ở tier NONE |
| Support efficient correction      | Hai nút**"Đã giải quyết được"** / **"Chưa đúng ý tôi"**              |
| Fail gracefully                   | Tier NONE tự**escalate** đúng người phụ trách thay vì bịa lời giải   |

---

# §5. Kiểu lỗi — 4 lớp chỗ khó + kịch bản (≥8)

| Lớp chỗ khó (taxonomy)    | Kịch bản rủi ro                                                   | Case kiểm thử                  |
| ------------------------- | ----------------------------------------------------------------- | ------------------------------ |
| ① Không có nguồn sự thật  | Câu hỏi quy định mới chưa có trong corpus → AI tự bịa             | TC-006, TC-007, TC-008, TC-009 |
| ② Mơ hồ / thiếu thông tin | Học viên nói "em bị lỗi này" → AI đoán bừa lỗi                    | TC-011, TC-012, TC-013, TC-014 |
| ③ Ngoài phạm vi           | Học viên hỏi tỷ số bóng đá / thời tiết → AI vẫn cố trả lời        | TC-040, TC-041, TC-042, TC-043 |
| ④ Đặc thù domain          | Ưu tiên câu trả lời**chưa xác minh** của học viên khác → hiểu sai | TC-015, TC-016, TC-017, TC-018 |

---

# §6. Bốn đường đi của trải nghiệm

### Happy Path (HIGH)

Tìm thấy thread giống (similarity ≥ 0.78) có verified answer → hiển thị trực tiếp, tự tin.

### Low Confidence (LOW)

Có topic match nhưng không direct match, hoặc nguồn chưa xác minh → báo "chưa chắc",
mời phản hồi, gắn nhãn cảnh báo nguồn.

### Failure / không căn cứ (NONE)

Không tìm thấy → nói thẳng "chưa có thread tương tự" và tự chuyển đúng người phụ trách.

### Correction (user sửa)

Bấm **"Chưa đúng ý tôi"** → chuyển tiếp đúng địa hạt (Admin / Mentor / LabCoach).

### Ngoài phạm vi

Câu tán gẫu / kiến thức chung / nhờ làm bài thay → từ chối lịch sự, **KHÔNG** làm phiền
người thật.

---

# §7. Kiểm thử

### Chiều chất lượng (định nghĩa kiểm chứng được)

Tìm đúng semantic · chống ảo giác (no-fabrication) · xử lý đầu vào rác · phân tầng nguồn
đúng — người ngoài nhóm chấm lại phải ra cùng kết quả.

### Golden Set

**56 case** nhóm tự xây (`src/test/test_cases.json`): ≥2 case/lớp chỗ khó + case thường

- case hiếm + case lấy từ chatlog thật.

### Quality Bar _(chốt trong spec, giữ nguyên)_

Đạt khi **≥ 70%** qua bộ **VÀ 100% không bịa** khi không có nguồn.

### Kết quả các lượt chạy

| Lượt  | Tổng thể      | Không bịa khi không có nguồn | Status                                    |
| ----- | ------------- | ---------------------------- | ----------------------------------------- |
| Lần 1 | 57.1% (32/56) | 0% (0/4)                     | **CRITICAL FAIL**                         |
| Lần 2 | 82% (46/56)   | 3/4                          | Đạt tổng thể; còn 1 case no-source cần vá |

_Phân tích nguyên nhân lần 1:_ pipeline chưa fail-closed về NONE và UI hiển thị NONE
giống HIGH → thông tin bịa trông đáng tin. Đã siết backend + phân biệt tier ở UI.

---

# §8. Phân công & kế hoạch _(6 người – 6 role · nhóm trưởng điền tên)_

| Thành viên             | Vai trò         | Công việc                                          |
| ---------------------- | --------------- | -------------------------------------------------- |
| **[TÊN THÀNH VIÊN 1]** | PM              | Quản lý dự án, AI Spec, Evidence, Evaluation, Demo |
| **[TÊN THÀNH VIÊN 2]** | Tool Developer  | Discord Bot, API, Semantic Search                  |
| **[TÊN THÀNH VIÊN 3]** | Core Developer  | Backend, Vector Database, Demo                     |
| **[TÊN THÀNH VIÊN 4]** | UI/UX           | Thiết kế giao diện, Prototype, Slide               |
| **[TÊN THÀNH VIÊN 5]** | Prompt Engineer | System Prompt, Guardrails, AI Summary              |
| **[TÊN THÀNH VIÊN 6]** | Data Engineer   | Thu thập dữ liệu, Embedding, Indexing              |

> **Testing (Golden Set / Test Case / Evaluation):** phụ trách chính **[TÊN THÀNH VIÊN 1]**
> (PM) + **[TÊN THÀNH VIÊN 6]** (Data Engineer).

### Willing Users

- **[TÊN WILLING USER 1]**
- **[TÊN WILLING USER 2]**
- **[TÊN WILLING USER 3]**

### Validation

**Câu hỏi**

1. Bot có gợi ý đúng thread bạn cần không?
2. Sau khi xem gợi ý, bạn có còn muốn đăng câu hỏi mới không?
3. Bạn mong bot cải thiện điều gì?

**Người ghi log:** **[TÊN THÀNH VIÊN 1]** và **[TÊN THÀNH VIÊN 6]**.

### Multi-prototype

- **Prototype A:** Semantic Search bằng Embedding.
- **Prototype B:** Semantic Search + LLM Reranking + AI Summary.

So sánh Precision@3, tỷ lệ không-bịa, thời gian phản hồi và mức độ hài lòng để chọn
phương án.

---

# §9. Changelog

| Thời điểm | Thay đổi                                  | Lý do (trỏ về feedback/case nào)           |
| --------- | ----------------------------------------- | ------------------------------------------ |
| CP2       | Xây Semantic Search                       | Giảm câu hỏi trùng                         |
| CP3       | Đo golden set lượt 1                      | Phát hiện CRITICAL FAIL 0/4 no-fabrication |
| CP4       | Fail-closed về NONE + phân biệt tier ở UI | Vá lỗi bịa khi không có nguồn (lượt 1)     |
| CP5       | Điều chỉnh ngưỡng similarity              | Giảm False Positive                        |
