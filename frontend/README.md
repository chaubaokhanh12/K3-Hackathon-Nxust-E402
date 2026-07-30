# DupBot — Semantic Duplicate Detection Bot for Discord Q&A

Prototype UI mô phỏng giao diện Discord cho bot phát hiện câu hỏi trùng ngữ nghĩa
trong kênh `#hoi-dap` của khoá.

## Chạy

```bash
cd demo
npm install
npm run dev
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
| Happy | similarity ≥ 42% | Đưa tối đa 3 thread kèm trích đoạn câu trả lời + 2 nút |
| Low-confidence | 20% ≤ similarity < 42% | Nói rõ "chỉ tìm được kết quả gần đúng" trước khi đưa gợi ý |
| Failure | similarity < 20% | Không đoán, chuyển LabCoach ngay, không bắt học viên bấm gì |
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

## Nối embedding thật

Chỉ cần thay thân hàm `searchSimilar` trong `src/lib/semanticSearch.js` — chữ ký
`async (query, { topK }) => { confidence, matches }` giữ nguyên nên UI không phải sửa:

```js
export async function searchSimilar(query, { topK = 3 } = {}) {
  const res = await fetch('/api/similar', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, topK }),
  })
  return res.json()
}
```

Backend: embed câu hỏi → cosine search trên vector store (pgvector / Qdrant) →
map score sang `confidence` bằng đúng hai ngưỡng `HIGH_THRESHOLD` / `LOW_THRESHOLD`
đang khai báo trong file này.

## Lưu ý

Toàn bộ nội dung thread, tên người và số liệu trong `data/threads.js` là **data giả
tự sinh** cho mục đích demo, không phải hội thoại thật của học viên.
