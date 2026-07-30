# AI SPEC — DupBot: Triage câu hỏi trùng lặp · Nhóm [XX] · Zone [X]
Hướng: [ ] A — VLearn  [x] B — Trợ lý Học viên  [ ] C — Làn mở
Loại: [ ] Tối ưu tính năng có sẵn  [x] Tính năng mới

## §1. User & Job
- Job executor + workflow: Học viên tìm kiếm hỗ trợ / LabCoach phản hồi câu hỏi trên Discord.
- Core JTBD: Tìm và đối chiếu ngay lập tức giải pháp từ các vấn đề tương tự đã được giải quyết trong quá khứ để không phải đợi.
- Problem statement: Học viên mất nhiều thời gian chờ đợi phản hồi cho các câu hỏi trùng lặp (những lỗi hoặc thắc mắc mà người khác đã gặp và được giải quyết).
- Evidence:
  - Số liệu mining: 82% thread thuộc một nhóm trùng lặp. 
  - Khảo sát: Trung vị thời gian chờ đợi để có câu trả lời đã xác minh là 522 phút (~9 tiếng).
  - ≥5 quote/ví dụ nguyên văn:
    - "phoenix không load được phần đội của tôi"
    - "sửa code trong folder /script có ảnh hưởng chấm điểm không?"
    - "deadline nộp sản phẩm cuối cùng là ngày nào"
    - "diem cong trên lớp có đổi thành xp không"
    - "lỗi font tiếng việt khi export pdf"

## §2. Impact & quyết định chọn
- Bảng impact ≥3 ứng viên:
  1. Semantic Search Thread cũ: Toàn bộ học viên x tần suất cao x tiết kiệm ~9 tiếng chờ/lần -> Khả thi cao.
  2. Tự động sinh câu trả lời mới hoàn toàn: Rủi ro sinh sai thông tin (ảo giác) quy định/deadline dẫn đến hậu quả trực tiếp -> Loại.
  3. Bản tin cuối ngày cho TA: Chỉ giúp TA, không giải quyết thời gian chờ thực tế của học viên -> Loại.
- Ứng viên ĐÃ LOẠI + vì sao: Sinh câu trả lời mới (ảo giác, rủi ro cao).
- Ứng viên CHỌN + vì sao: Phân loại và đề xuất thread cũ đã được xác minh (HIGH/LOW/NONE) (tiết kiệm thời gian, dựa trên nguồn thực tế).

## §3. Giải pháp tương tự đã nghiên cứu
- [Discord Search gốc]: Tìm bằng keyword thường miss vì khác cách diễn đạt / không phân tầng được nguồn trả lời đúng. DupBot khác biệt nhờ Semantic Search và phân tầng nguồn.
- [AI Chatbot thông thường]: Thường cố gắng tự sinh câu trả lời mới (hallucinate). DupBot chỉ lấy snippet nguyên văn và có 3 tier confidence.

## §4. Thiết kế
- Lát cắt MỘT CÂU: Học viên đặt câu hỏi, AI phân loại mức độ tương đồng (HIGH/LOW/NONE) với các thread cũ và đề xuất tối đa 3 thread đã giải quyết hoặc tự động chuyển LabCoach.
- Non-goals: 
  1. KHÔNG giảng bài mới, KHÔNG giải thích dài dòng.
  2. KHÔNG tự bịa hoặc viết lại câu trả lời (chỉ dùng snippet verbatim).
  3. KHÔNG trả lời các câu hỏi ngoài phạm vi khóa học.
- Mức prototype nhắm tới: [ ] Sketch [ ] Mock [x] Working — backend tool kết nối frontend thật.
- Automation: [x] conditional (có threshold cho HIGH/LOW/NONE) — lý do theo cost-of-error: sai thông tin quy định làm học viên mất điểm, nên fail-closed (NONE).
- §4b. Nguyên tắc đã áp dụng:
  | Nguyên tắc | Áp cụ thể vào đâu trong prototype |
  |---|---|
  | Match system to real world | Giao diện trả về dạng Card có Confidence, Excerpt, AnsweredBy |
  | Make clear what system can do | Phân loại rõ HIGH, LOW, NONE và nói "không biết" khi ở tier NONE |
  | Support efficient correction | Nút "Đã giải quyết được" / "Chưa đúng ý tôi" |
  | Fail gracefully | Tự động escalate to LabCoach nếu không tìm thấy thread (NONE) |

## §5. Kiểu lỗi — 4 lớp chỗ khó + kịch bản (≥8)
| Lớp chỗ khó | Kịch bản rủi ro | Case kiểm thử |
|---|---|---|
| ① Không có nguồn sự thật | Câu hỏi về quy định mới chưa có trong corpus, AI tự bịa câu trả lời | TC-006, TC-007, TC-008, TC-009 |
| ② Mơ hồ/Thiếu thông tin | Học viên nói "em bị lỗi này", AI đoán bừa lỗi | TC-011, TC-012, TC-013, TC-014 |
| ③ Ngoài phạm vi | Học viên hỏi tỷ số bóng đá / thời tiết | TC-040, TC-041, TC-042, TC-043 |
| ④ Đặc thù domain | Ưu tiên câu trả lời chưa xác minh của học viên khác dẫn đến hiểu sai | TC-015, TC-016, TC-017, TC-018 |

## §6. Bốn đường đi của trải nghiệm
- Happy path (HIGH): Tìm thấy thread giống (similarity ≥ 0.78) có verified answer -> Hiển thị trực tiếp và tự tin.
- Low-confidence (LOW): Có topic match nhưng không direct match, hoặc chưa xác minh -> Báo chưa chắc chắn, mời phản hồi.
- Failure/không căn cứ (NONE): Không tìm thấy -> Nói "không biết" và escalate LabCoach.
- Correction (user sửa): Ấn nút "Chưa đúng ý tôi" -> Chuyển LabCoach.

## §7. Kiểm thử
- Chiều chất lượng + định nghĩa kiểm chứng được: Đánh giá theo khả năng tìm đúng semantic, chống ảo giác, xử lý đầu vào rác, và phân tầng nguồn.
- Golden set: 56 cases (file trong `src/test/test_cases.json`).
- Quality bar: "Đạt khi ≥ 70% qua bộ, và 100% không bịa khi không có nguồn"
- Kết quả các lượt chạy:
  | Lượt | Tổng thể | Không bịa khi không có nguồn | Status |
  |---|---|---|---|
  | Lần 1 | 57.1% (32/56) | 0% (0/4) | ❌ CRITICAL FAIL |
  | Lần 2 (Dự kiến) | TBD | TBD | TBD |

## §8. Phân công & kế hoạch
- Phân công có tên: 
  - Spec & Evidence: [Tên thành viên]
  - Prompt & Logic: [Tên thành viên]
  - Code & Tích hợp: [Tên thành viên]
  - Demo: [Tên thành viên]
- Willing users: [Tên 3 người thật] + kế hoạch vòng validation CP5
- Multi-prototype: [Không áp dụng]

## §9. Changelog
| Thời điểm | Đổi gì | Vì sao (trỏ về feedback/case nào) |
|---|---|---|
| [Hiện tại] | Tạo bản Spec ban đầu | Dựa trên kết quả test CP3 |
