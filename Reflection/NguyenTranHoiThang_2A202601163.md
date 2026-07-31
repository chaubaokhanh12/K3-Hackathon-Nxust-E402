# Reflection cá nhân

- **Họ tên:** Nguyễn Trần Hội Thắng
- **Mã học viên:** 2A202601163
- **Nhóm / Dự án:** DupBot — Triage câu hỏi trùng lặp trên Discord khoá AI Thực Chiến
- **Vai trò:** UI/UX — Thiết kế giao diện, Prototype, Slide

---

## 1. Vai trò và phần mình làm

Mình phụ trách mảng UI/UX: dựng giao diện mô phỏng kênh "Hỏi đáp" Discord và biến các
quyết định của backend thành thứ học viên nhìn thấy và bấm được.

Cụ thể phần có tên mình trong repo:

- **Giao diện mô phỏng Discord** (`frontend/`): layout kênh chat, khung nhập tin,
  danh sách server/kênh, để demo chạy đúng bối cảnh thật học viên đang dùng thay vì
  một form tra cứu khô khan.
- **Card kết quả theo 3 tier confidence** (khớp §4b spec): mỗi gợi ý hiển thị dạng
  thẻ có **Confidence** (HIGH / LOW / NONE), **Excerpt** (trích đoạn nguyên văn),
  và **AnsweredBy** (người trả lời + vai trò). Đây là chỗ mình áp nguyên tắc
  *Match system to real world* và *Make clear what the system can do*: nhìn màu và
  nhãn là biết bot chắc hay không chắc.
- **Bốn đường đi trải nghiệm trong UI** (khớp §6 spec): happy (HIGH) hiển thị trực
  tiếp, low-confidence (LOW) báo "chưa chắc" và mời phản hồi, failure (NONE) nói thẳng
  "chưa có" + tự chuyển người phụ trách, correction là hai nút **"Đã giải quyết được"**
  / **"Chưa đúng ý tôi"** để học viên sửa hướng.
- **Tính năng @mention với gợi ý tự động** kiểu Discord, và **Slide demo** cho vòng
  trình bày.

## 2. AI hỗ trợ mình thế nào

- **Dựng frontend nhanh hơn nhiều:** mình dùng AI để scaffold React/Vite + Tailwind,
  sinh các component (Card, Composer, MessageList, autocomplete @mention) rồi mình
  đọc lại, sửa layout, chỉnh màu tier và luồng state cho khớp thiết kế. AI lo phần
  code lặp, mình giữ quyền quyết định về trải nghiệm.
- **Đối chiếu UI với contract của backend:** mình nhờ AI so nhãn/field trên Card với
  payload thật mà `bot.py` trả ra (`confidence`, `suggestions`, `excerpt`,
  `source_tier`, nút render), để giao diện không hiển thị sai so với điều bot thực sự
  tính.
- **Kiểm thử giao diện:** AI giúp viết test cho phần autocomplete và luồng gửi tin,
  bắt được vài lỗi jsdom và một bug dữ liệu người-được-mention bị phân mảnh — mình
  hợp nhất lại một nguồn dữ liệu.

Bài học về cách dùng AI: mình học được rằng **mô tả rõ contract (đầu vào/đầu ra) rồi
mới nhờ AI code** thì kết quả bám sát hơn hẳn so với mô tả chung chung; và luôn phải
tự đọc lại code AI sinh — có chỗ nó tạo giao diện "trông ổn" nhưng không phản ánh
đúng trạng thái thật của bot (xem mục 3).

## 3. Một bài học từ case fail của chính nhóm

**Case fail:** Ở lượt đo đầu tiên (CP3), golden set cho kết quả **57.1% (32/56)** tổng
thể và **0% (0/4)** ở tiêu chí quan trọng nhất — *"không bịa khi không có nguồn"* —
bị đánh dấu **CRITICAL FAIL** (spec §7). Nghĩa là với 4 câu hỏi không hề có thread
nguồn (ví dụ *"deadline nộp sản phẩm cuối cùng là ngày nào"*), bot vẫn nặn ra câu
trả lời nghe rất tự tin.

**Vì sao mình thấy đây là bài học của riêng mình (UI/UX), không chỉ của backend:**
giao diện lúc đó **đối xử NONE giống HIGH** — vẫn đổ ra 3 card gợi ý trông chắc nịch,
không có tín hiệu thị giác nào cảnh báo "đây là phỏng đoán". Tức là **chính UI đã tiếp
tay làm cho thông tin bịa trông đáng tin.** Với dự án mà sai một câu về quy định/deadline
là học viên mất điểm thật, đây là lỗi nặng chứ không phải lỗi thẩm mỹ.

**Mình đã đổi gì:** tách bạch hẳn 3 tier ở tầng giao diện — NONE không được render card
lời giải, chỉ hiển thị thông báo "chưa có thread tương tự" kèm việc tự chuyển người phụ
trách; LOW phải mang sắc thái "gần đúng, chưa chắc" khác rõ với HIGH; nguồn chưa xác
minh phải có nhãn cảnh báo riêng. Đây chính là hai nguyên tắc *Make clear what the
system can do* và *Fail gracefully* trong §4b — trước đó mình mới làm đúng ở happy path,
chưa làm đủ ở failure path. Sau khi cả nhóm siết lại (backend fail-closed về NONE + UI
trung thực theo tier), lượt 2 lên **82% (46/56)** và **3/4** ở tiêu chí no-fabrication.

**Điều mình rút ra:** giao diện của một sản phẩm AI không chỉ để đẹp — nó phải **trung
thực về độ chắc chắn của AI**. Một UI đẹp mà che giấu sự "không biết" của mô hình còn
nguy hiểm hơn một UI xấu nhưng thành thật. Từ giờ khi thiết kế, mình đặt câu hỏi
"trạng thái tệ nhất (bot sai / bot không biết) trông thế nào trên màn hình?" **trước**
khi trau chuốt trạng thái đẹp nhất.

---

*Mình sẵn sàng giải thích trực tiếp mọi phần có tên mình ở CP5/CP6.*
