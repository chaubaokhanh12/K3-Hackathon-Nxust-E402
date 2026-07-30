# DupBot — Semantic Duplicate Detection Bot for Discord Q&A

Prototype UI mô phỏng giao diện Discord cho bot phát hiện câu hỏi trùng ngữ nghĩa
trong kênh `#hoi-dap` của khoá.

## Chạy

Chạy cả backend và frontend từ project root:

```powershell
.\start-dev.ps1
```

Hoặc chỉ chạy UI bằng mock browser:

```bash
cd frontend
npm install
VITE_USE_MOCK=true npm run dev
```

Mở http://localhost:5173

## Lát cắt được build

> **Một học viên** đăng câu hỏi mới trong `#hoi-dap` · **bot quyết định** câu hỏi này
> đã có lời giải trong lịch sử kênh hay chưa · **kết quả** là học viên tự đọc được
> câu trả lời cũ, hoặc LabCoach nhận thread kèm ngữ cảnh sẵn.

Học viên không phải học thêm thao tác nào — vẫn gõ câu hỏi như bình thường.

## Bốn đường đi trải nghiệm

| Đường đi | Điều kiện | Bot làm gì |
|---|---|---|
| Happy | Có direct match đã xác minh | Đưa tối đa 3 thread kèm trích đoạn nguồn + 2 nút |
| Low-confidence | Direct chưa xác minh hoặc chỉ cùng topic | Cảnh báo rõ; topic-only không được trình như lời giải |
| Failure | Không có direct/topic đủ ngưỡng | Không đoán, chuyển LabCoach ngay, không bắt học viên bấm gì |
| Correction | học viên bấm "Chưa đúng ý tôi" | Tag `@LabCoach` kèm câu hỏi gốc + danh sách thread đã bị loại + lý do |

Bốn câu mẫu ứng với bốn đường đi có sẵn dưới ô nhập tin.

## Hai nút cuối tin nhắn bot

- **Đã giải quyết được** → thread gắn nhãn `Đã xử lý`, rời hàng chờ, LabCoach không cần vào.
- **Chưa đúng ý tôi** → bot tag LabCoach kèm ngữ cảnh, thread gắn nhãn `Chờ LabCoach`.

## Cấu trúc

```
src/
  App.jsx                    state của kênh + điều phối 4 đường đi
  lib/semanticSearch.js      mô phỏng embedding search (điểm nối API thật)
  data/threads.js            10 thread đã có lời giải + member list (data giả)
  components/
    ServerRail.jsx           cột server ngoài cùng
    ChannelSidebar.jsx       danh sách kênh
    ChannelHeader.jsx        header dùng chung cho mọi kênh (icon/tiêu đề/topic đổi theo kênh)
    HoiDapChannel.jsx        toàn bộ luồng DupBot cho #hoi-dap (đã tách khỏi App.jsx)
    ChannelIntro.jsx         phần đầu kênh #hoi-dap
    UserMessage.jsx          tin nhắn người thật
    BotMessage.jsx           thẻ gợi ý của bot + 2 nút
    SimilarThreadCard.jsx    một thread gợi ý (thanh similarity + trích đoạn)
    EscalationMessage.jsx    tin nhắn tag LabCoach kèm ngữ cảnh
    SystemMessage.jsx        dòng hệ thống khi gắn nhãn thread
    TypingIndicator.jsx      trạng thái bot đang tìm
    MessageComposer.jsx      ô nhập tin của #hoi-dap + câu mẫu 4 đường đi
    GeneralChannel.jsx       #chung — chat thường, không có bot
    ForumChannel.jsx         #chia-se — danh sách bài đăng + chi tiết 1 bài
    InfoChannel.jsx          #bai-hoc — thông báo buổi học, chỉ đọc
    PlaceholderChannel.jsx   kênh có thật ngoài Discord nhưng ngoài lát cắt prototype
    SimpleComposer.jsx       ô nhập tin dùng chung cho #chung
    MemberList.jsx           cột thành viên
```

## Điều hướng nhiều kênh

Sidebar (`ChannelSidebar.jsx`) đọc danh sách kênh từ `data/channels.js` và gọi
`onSelectChannel(id)` khi bấm — `App.jsx` chuyển kênh bằng cách đổi `activeChannelId`
rồi switch sang đúng component theo `channel.kind`:

| Kênh | kind | Component |
|---|---|---|
| #chung | `chat` | `GeneralChannel` |
| #hoi-dap | `qa` | `HoiDapChannel` (DupBot) |
| #chia-se | `forum` | `ForumChannel` |
| #bai-hoc | `info` | `InfoChannel` |
| còn lại (gioi-thieu, thong-bao...) | `placeholder` | `PlaceholderChannel` |

Bấm vào tiêu đề bài đăng dưới `#chia-se` trong sidebar mở thẳng bài đó (giống Discord
forum channel thật). Toàn bộ data ở các kênh này là giả, sinh riêng cho demo — không
phải nội dung thật của học viên/giảng viên.

## Backend thật

`src/services/dupbotService.js` mặc định gọi `/api`. Vite proxy endpoint này sang
FastAPI ở port 8000. `src/lib/semanticSearch.js` chỉ còn là fallback khi bật
`VITE_USE_MOCK=true`; nó không được dùng trong demo tích hợp.

Backend dùng OpenAI Embeddings khi có `OPENAI_API_KEY`. Nếu thiếu key, backend dùng
fallback corpus cục bộ và trả `retrieval_mode=local-corpus-fallback` để UI không
nhận nhầm đây là lượt gọi AI thật.

## Tính năng @ mention

Gõ `@` trong bất kỳ ô nhập tin nào (MessageComposer của #hoi-dap, SimpleComposer của
các kênh khác) sẽ mở dropdown gợi ý thành viên — lọc theo ký tự gõ tiếp theo, điều
hướng bằng phím lên/xuống, Enter/Tab để chọn, Esc để đóng. Chọn xong chèn token
`@[Tên]` đúng vị trí con trỏ; khi hiển thị, token này được `MentionText.jsx` render
thành pill giống mention thật của Discord.

- `data/mentionable.js` gộp danh sách người có thể tag từ mọi file data (threads,
  generalChat, forumPosts, lessons) — dedupe theo tên, kể cả role đặc biệt
  `@everyone`, `@LabCoach`, `@Mod`.
- `hooks/useMentionAutocomplete.js` chứa toàn bộ logic phát hiện trigger, lọc gợi ý,
  điều hướng bàn phím — dùng chung cho mọi composer thay vì lặp code.
- `lib/mentions.js` định nghĩa định dạng lưu trữ `@[Tên]` và hàm parse thành segment
  text/mention để render.

## Trang trí thêm cho giống Discord thật

- Category trong sidebar bấm được để thu gọn/mở rộng (chevron xoay), giống hành vi
  thật của Discord.
- Bottom user panel có icon mic (bấm để mute/unmute, đổi màu đỏ khi tắt), tai nghe,
  cài đặt — giống thanh trạng thái người dùng thật.
- Server rail có badge số tin chưa đọc trên icon server.
- Tin nhắn hỗ trợ preview "đang trả lời" (reply reference) phía trên nội dung, xem ví
  dụ trong `data/generalChat.js`.

## Lưu ý

Toàn bộ nội dung thread, tên người và số liệu trong `data/threads.js` là **data giả
tự sinh** cho mục đích demo, không phải hội thoại thật của học viên.
