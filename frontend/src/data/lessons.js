/** Data giả cho kênh thông báo #bai-hoc — chỉ giảng viên/Admin đăng, học viên đọc. */

export const LESSON_POSTS = [
  {
    id: 'l1',
    title: 'Buổi 5 — Mini Hackathon kickoff',
    author: 'Admin Phương',
    role: 'ADMIN',
    avatarColor: '#ed93b1',
    time: 'Hôm nay lúc 08:00',
    body: 'Đề bài, rubric và data pack đã có trong repo. Đọc kỹ mục "Ràng buộc chung" trong 01-de-bai.md trước khi chọn hướng A/B/C.',
  },
  {
    id: 'l2',
    title: 'Buổi 4 — Prompt engineering nâng cao',
    author: 'Giảng viên An',
    role: 'LABCOACH',
    avatarColor: '#c0dd97',
    time: '2 ngày trước',
    body: 'Slide và recording buổi 4 đã up vào #chia-se-tai-lieu. Bài tập về nhà nộp trước buổi 5, xem chi tiết ở #bai-tap.',
  },
  {
    id: 'l3',
    title: 'Buổi 3 — RAG và vector database',
    author: 'Giảng viên An',
    role: 'LABCOACH',
    avatarColor: '#c0dd97',
    time: '4 ngày trước',
    body: 'Recap buổi 3: chunking strategy, chọn embedding model, và cách đánh giá retrieval quality bằng recall@k.',
  },
  {
    id: 'l4',
    title: 'Buổi 2 — Xây pipeline đánh giá LLM',
    author: 'Admin Phương',
    role: 'ADMIN',
    avatarColor: '#ed93b1',
    time: '6 ngày trước',
    body: 'Đã sửa lỗi link Colab buổi 2, các bạn tải lại notebook mới nếu notebook cũ báo lỗi import.',
  },
]
