# discord_qa_mock.json — mô tả cấu trúc

71 thread, 24 nhóm trùng lặp, 55 câu truy vấn test. Sinh từ 19 cặp Q-A thật, toàn bộ tên người dùng là tổng hợp.

## Cây dữ liệu

```
meta                 thông tin guild / channel
roles                role_id -> { name, verified_source }
users[]              35 người: 30 Learner, 3 LabCoach, 1 Mentor, 1 Admin
threads[]            71 thread, ĐƠN VỊ INDEX
duplicate_groups[]   ground truth: thread nào hỏi cùng vấn đề
test_queries[]       55 truy vấn kèm đáp án để chấm benchmark
```

## threads[] — đơn vị index

| Trường | Dùng để làm gì |
|---|---|
| `thread_id` | khóa chính, cũng là message_id của câu hỏi gốc |
| `title` | tiêu đề forum post, nên gộp vào text đem đi embed |
| `topic_id` | cụm chủ đề, tiện lọc lúc debug |
| `tag` | Vận hành / Team / Điểm số / Kỹ thuật / Dự án / Tài nguyên / Lịch trình / Khác |
| `link` | link nhảy thẳng vào thread, đây là thứ bot trả về cho người hỏi |
| `question` | message gốc: content, author, có ảnh không, có code block không |
| `replies[]` | các câu trả lời, đã kèm role và cờ `is_verified_source` |
| `verified_answer` | có câu trả lời từ LabCoach/Mentor/Admin hay không |
| `trust` | trỏ thẳng tới câu trả lời được gắn nhãn: message_id, ai trả lời, role, link |
| `first_response_minutes` | phút tới câu trả lời đầu tiên |
| `verified_response_minutes` | phút tới câu trả lời đã xác minh |

Text gợi ý đem đi embed: `title + "\n" + question.content`. Nối thêm replies thì recall tăng nhưng dễ nhiễu, nên thử cả hai rồi so.

## Phân tầng nguồn

`roles[].verified_source` là True với LabCoach, Mentor, Admin, BTC. Learner là False.

Khi trả kết quả, xếp thread có `verified_answer = true` lên trước, và lấy `trust.link` làm link chính. Thread chỉ có học viên trả lời vẫn trả về nhưng ghi rõ chưa được xác minh.

## Chấm benchmark

`test_queries[]` có bốn loại trong trường `query_type`:

- `dien_giai` — hỏi bằng từ khác hẳn, keyword search trượt. Đây là phần chứng minh giá trị sản phẩm.
- `keyword` — trùng từ khóa, cả hai cách đều tìm được. Dùng làm nhóm đối chứng.
- `khong_co_dap_an` — không có thread nào trả lời được, `expected_thread_ids` rỗng. Bot phải nói không biết. Nếu bot vẫn trả về 3 gợi ý thì đó là lỗi nặng nhất và phải bị tính là sai.
- Trường `keyword_search_hits` cho biết baseline có bắt được không, dùng để tự sinh bảng so hai cột mà không phải chấm tay.

Cách chấm: hit@3 nghĩa là có ít nhất một `expected_thread_ids` nằm trong 3 kết quả trả về. Với `khong_co_dap_an` thì tính đúng khi bot trả về rỗng hoặc từ chối.

## Những ca xấu đã cố tình nhét vào

Đây là phần quan trọng nhất, vì mock sạch quá thì benchmark vô nghĩa.

- 4 thread không ai trả lời
- 2 thread chỉ có ảnh chụp màn hình, câu hỏi kiểu "e bị lỗi này ạ" không có thông tin gì. Một trong hai bị gắn `no_dup` vì không thể xác định ground truth. Đây là ca thất bại bắt buộc phải đem ra nói khi pitch.
- 38 thread chỉ có học viên trả lời, không ai xác minh
- Các reply nhiễu: "up ạ", "e cũng bị v", "mình cũng bị y chang"
- Vài câu trả lời rất dài do học viên dán từ AI ra, đúng như trong data thật
- Tiếng Việt lẫn thuật ngữ Anh, viết tắt, không dấu lẫn có dấu
- 13 thread lẻ không thuộc nhóm trùng nào, để bot phải phân biệt được lúc nào nên im lặng

## Số liệu rút ra được từ chính bộ này

Có thể đưa thẳng lên slide, và nói rõ đây là số trên corpus tổng hợp:

- 82% thread thuộc một nhóm trùng lặp
- 41% thread có câu trả lời đã xác minh, 54% chỉ có học viên trả lời
- Trung vị chờ phản hồi đầu tiên khoảng 51 phút
- Trung vị chờ câu trả lời đã xác minh khoảng 522 phút, tức gần 9 tiếng

Con số cuối là luận điểm mạnh nhất: học viên chờ gần một ngày cho câu trả lời đáng tin, trong khi phần lớn vấn đề đã có lời giải nằm sẵn ở thread cũ.

## Đọc file

```python
import json
d = json.load(open("discord_qa_mock.json", encoding="utf-8"))

docs = [{
    "id": t["thread_id"],
    "text": t["title"] + "\n" + t["question"]["content"],
    "verified": t["verified_answer"],
    "link": (t["trust"] or {}).get("link", t["link"]),
} for t in d["threads"]]
```
