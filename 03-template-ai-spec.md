# AI SPEC — Semantic Duplicate Detection Bot for Discord Q&A · Nhóm XX · Zone X

Hướng: ☑ B — Trợ lý Học viên
Loại: ☑ Tính năng mới

---

# §1. User & Job

### Job executor + workflow

**Người dùng:** Thành viên trong cộng đồng sử dụng Discord (CLB, nhóm học tập, dự án, cộng đồng công nghệ,...).

**Workflow**
1. Người dùng cần hỏi một vấn đề hoặc tìm kiếm thông tin.
2. Nhập câu hỏi vào kênh Discord.
3. Bot tự động phân tích nội dung câu hỏi.
4. Bot tìm các cuộc thảo luận có nội dung tương tự bằng Semantic Search.
5. Nếu tìm thấy kết quả phù hợp, bot gợi ý các bài viết liên quan và tóm tắt ngắn nội dung.
6. Người dùng quyết định đọc lại bài cũ hoặc tiếp tục đăng câu hỏi mới.

### Core JTBD

>Khi muốn đặt câu hỏi trong cộng đồng Discord, tôi muốn biết liệu vấn đề của mình đã từng được hỏi trước đó hay chưa để có thể nhận được câu trả lời nhanh hơn và tránh tạo ra các bài đăng trùng lặp.

### Problem Statement

Trong nhiều cộng đồng Discord, cùng một nội dung thường được hỏi nhiều lần do người dùng khó tìm lại các cuộc thảo luận cũ hoặc không biết chúng đã tồn tại. Điều này làm kênh trò chuyện trở nên lộn xộn, tăng số lượng bài đăng trùng lặp và khiến người hỗ trợ phải trả lời cùng một vấn đề nhiều lần.

### Evidence

- Khảo sát người dùng về hành vi tìm kiếm thông tin trên Discord.
- Phân tích lịch sử tin nhắn để thống kê số lượng câu hỏi có nội dung tương tự.
- Thu thập phản hồi của quản trị viên và thành viên về tình trạng câu hỏi lặp lại.
- (Bổ sung số liệu sau khi hoàn thành khảo sát.)

---

# §2. Impact & Quyết định chọn

| Ứng viên | Mức ảnh hưởng | Khả thi |
|-----------|---------------|----------|
| Semantic Duplicate Detection Bot | Cao | Cao |
| AI Assistant trả lời câu hỏi | Rất cao | Trung bình |
| AI Summary cuộc thảo luận | Trung bình | Cao |

### Ứng viên đã loại

**AI Assistant trả lời mọi câu hỏi**

- Phạm vi quá rộng.
- Phụ thuộc nhiều vào chất lượng dữ liệu.
- Khó đánh giá đúng/sai.
- Chi phí triển khai và kiểm thử cao.

### Ứng viên được chọn

**Semantic Duplicate Detection Bot**

Lý do:
- Giải quyết trực tiếp vấn đề câu hỏi trùng lặp.
- Giảm thời gian tìm kiếm thông tin.
- Giảm khối lượng trả lời lặp lại của quản trị viên và cộng đồng.
- Dễ đánh giá bằng Precision, Recall và tỷ lệ giảm số bài đăng trùng.

---

# §3. Giải pháp tương tự đã nghiên cứu

### Discord Search

**Đáng học**
- Tìm kiếm nhanh.
- Có sẵn trên Discord.

**Đáng né**
- Chỉ dựa trên từ khóa.
- Không hiểu ngữ nghĩa.

---

### Stack Overflow - Similar Questions

**Đáng học**
- Gợi ý câu hỏi tương tự trước khi đăng.

**Đáng né**
- Phụ thuộc nhiều vào tiêu đề.
- Không tối ưu cho Discord.

---

### Điểm khác biệt

Sản phẩm sử dụng Semantic Search để hiểu ý nghĩa câu hỏi thay vì chỉ so khớp từ khóa, giúp phát hiện các câu hỏi được diễn đạt theo nhiều cách khác nhau. Bot còn tóm tắt ngắn nội dung của các cuộc thảo luận liên quan để người dùng quyết định có cần đăng câu hỏi mới hay không.

---

# §4. Thiết kế

### Lát cắt

>Khi một thành viên chuẩn bị gửi câu hỏi trên Discord, bot tự động kiểm tra xem câu hỏi có trùng ngữ nghĩa với các cuộc thảo luận trước đó hay không và gợi ý những bài viết liên quan để người dùng quyết định có tiếp tục đăng câu hỏi mới.

### Non-goals

- Không thay thế người hỗ trợ trả lời.
- Không tự động trả lời mọi câu hỏi.
- Không kiểm duyệt nội dung.
- Không đánh giá đúng sai của câu hỏi.

### Prototype

☑ Working Prototype

**Thành phần thật**
- Discord Bot
- Semantic Search
- Vector Database

**Mock**
- AI Summary (nếu chưa hoàn thiện)

### Automation

☑ Conditional Automation

Bot chỉ đưa ra gợi ý khi độ tương đồng vượt ngưỡng đã xác định. Người dùng vẫn là người quyết định cuối cùng nhằm hạn chế ảnh hưởng của các trường hợp AI nhận diện sai.

### Nguyên tắc

| Nguyên tắc | Áp dụng |
|------------|----------|
| Human Control | Người dùng quyết định có đăng câu hỏi mới hay không |
| Explainability | Hiển thị điểm tương đồng và bài viết được tìm thấy |
| Error Prevention | Gợi ý trước khi gửi câu hỏi |
| Progressive Disclosure | Chỉ hiển thị chi tiết khi có kết quả phù hợp |

---

# §5. Kiểu lỗi

### 1. Nhận diện sai câu hỏi trùng

- Hai câu hỏi khác nhau nhưng bị đánh giá là trùng.
- Bot gợi ý bài viết không liên quan.

### 2. Bỏ sót câu hỏi trùng

- Hai câu hỏi có cùng ý nghĩa nhưng bot không phát hiện.
- Người dùng diễn đạt khác khiến embedding không nhận ra.

### 3. Dữ liệu chưa đầy đủ

- Chưa có bài viết liên quan.
- Nội dung cũ đã lỗi thời.
- Dữ liệu chưa được lập chỉ mục.

### 4. Đầu vào khó xử lý

- Câu hỏi quá ngắn.
- Chỉ gửi hình ảnh.
- Viết tắt hoặc tiếng lóng.
- Thiếu ngữ cảnh.

---

# §6. Bốn đường đi của trải nghiệm

### Happy Path

Bot tìm thấy các cuộc thảo luận liên quan → hiển thị 3 kết quả phù hợp → người dùng đọc câu trả lời cũ → không cần đăng câu hỏi mới.

### Low Confidence

Bot tìm thấy kết quả có độ tương đồng trung bình → thông báo đây chỉ là gợi ý → người dùng quyết định tiếp tục đăng hoặc xem bài cũ.

### Failure

Không tìm thấy kết quả phù hợp → bot thông báo chưa có nội dung tương tự và cho phép đăng câu hỏi.

### Correction

Người dùng bổ sung thêm thông tin hoặc chỉnh sửa câu hỏi → bot thực hiện tìm kiếm lại → đưa ra kết quả chính xác hơn.

### Ngoài phạm vi

Bot không xử lý các yêu cầu không phải câu hỏi hoặc không liên quan đến nội dung của cộng đồng.

### Domain đặc thù

Bot hỗ trợ các thuật ngữ riêng của từng cộng đồng thông qua embedding và dữ liệu đã được lập chỉ mục.

---

# §7. Kiểm thử

### Chỉ số

- Precision@3
- Recall
- Top-1 Accuracy
- Thời gian phản hồi
- Mức độ hài lòng của người dùng

### Golden Set

20 trường hợp kiểm thử gồm:

- 5 câu hỏi trùng hoàn toàn.
- 5 câu hỏi diễn đạt khác nhau.
- 5 câu hỏi không liên quan.
- 5 câu hỏi mơ hồ hoặc thiếu ngữ cảnh.

### Quality Bar

Đạt khi:

- Precision@3 ≥ 85%.
- Recall ≥ 80%.
- Thời gian phản hồi ≤ 2 giây.

---

# §8. Phân công & kế hoạch

| Thành viên | Vai trò | Công việc |
|------------|----------|-----------|
| Châu | PM | Quản lý dự án, AI Spec, Evidence, Evaluation, Demo |
| Khải | Tool Developer | Discord Bot, API, Semantic Search |
| Tâm | Core Developer | Backend, Vector Database, Demo |
| Thắng | UI/UX | Thiết kế giao diện, Prototype, Slide |
| An | Prompt Engineer | System Prompt, Guardrails, AI Summary |
| Đạt | Data Engineer | Thu thập dữ liệu, Embedding, Indexing |
| Châu + Đạt | Testing | Golden Set, Test Case, Evaluation |

### Willing Users

- User 1
- User 2
- User 3

### Validation

**Câu hỏi**
1. Bot có gợi ý đúng cuộc thảo luận bạn cần không?
2. Bạn có còn muốn đăng câu hỏi mới sau khi xem gợi ý không?
3. Bạn mong muốn bot cải thiện điều gì?

**Người ghi log:** Châu và Đạt.

### Multi-prototype

**Prototype A**
- Semantic Search bằng Embedding.

**Prototype B**
- Semantic Search + LLM Reranking + AI Summary.

So sánh Precision, Recall, thời gian phản hồi và mức độ hài lòng của người dùng để lựa chọn phương án phù hợp.

---

# §9. Changelog

| Thời điểm | Thay đổi | Lý do |
|------------|----------|-------|
| CP2 | Xây dựng Semantic Search | Giảm câu hỏi trùng |
| CP4 | Bổ sung AI Summary | Tăng tốc độ đọc kết quả |
| CP5 | Điều chỉnh ngưỡng Similarity | Giảm False Positive |
