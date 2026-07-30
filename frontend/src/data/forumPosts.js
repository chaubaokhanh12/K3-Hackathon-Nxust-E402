/** Data giả cho kênh forum #chia-se — 3 tiêu đề đầu lấy đúng từ ảnh chụp kênh thật của user. */

export const FORUM_POSTS = [
  {
    id: 'f1',
    title: 'Sử dụng Claude Code với Claude Opus',
    author: 'Minh Đức',
    avatarColor: '#7f77dd',
    tag: 'Công cụ',
    replies: 12,
    views: 340,
    time: '2 giờ trước',
    excerpt:
      'Mình vừa thử Claude Code kết hợp Opus để refactor một codebase Next.js khá lớn, tốc độ và độ chính xác hơn hẳn so với Sonnet cho task nhiều file. Chia sẻ vài prompt mình dùng...',
    replyThread: [
      { author: 'Gia Hân', avatarColor: '#5dcaa5', body: 'Bạn có so sánh chi phí không, Opus đắt hơn Sonnet khá nhiều mà' },
      { author: 'Minh Đức', avatarColor: '#7f77dd', body: 'Có, task refactor lớn thì đáng, task nhỏ mình vẫn dùng Sonnet cho rẻ' },
    ],
  },
  {
    id: 'f2',
    title: '[AI Tips] Kiểm tra máy có chạy được LLM local không',
    author: 'Gia Hân',
    avatarColor: '#5dcaa5',
    tag: 'Tips',
    replies: 8,
    views: 210,
    time: '4 giờ trước',
    excerpt:
      'Trước khi cài Ollama hay chạy model local, chạy lệnh này để kiểm tra VRAM và RAM khả dụng, đỡ mất công tải model 8B rồi máy đứng hình...',
    replyThread: [
      { author: 'Nam Khánh', avatarColor: '#85b7eb', body: 'Máy mình 8GB VRAM chạy 7B ổn không nhỉ' },
      { author: 'Gia Hân', avatarColor: '#5dcaa5', body: 'Ổn với bản quantize 4-bit, full precision thì hơi căng' },
    ],
  },
  {
    id: 'f3',
    title: 'KIMI K3 chính thức lên Huggingface',
    author: 'Đức Anh',
    avatarColor: '#f0997b',
    tag: 'Tin tức',
    replies: 21,
    views: 512,
    time: '6 giờ trước',
    excerpt:
      'Model KIMI K3 vừa được Moonshot AI public trên Huggingface, benchmark cho thấy vượt trội ở tác vụ coding và tiếng Trung. Ai đã thử chưa?',
    replyThread: [
      { author: 'Bảo Trâm', avatarColor: '#fac775', body: 'Mình thử rồi, code Python khá ổn nhưng tiếng Việt còn yếu' },
    ],
  },
  {
    id: 'f4',
    title: 'So sánh chi phí GPT-4o vs Claude Sonnet cho task tóm tắt',
    author: 'Thuỳ Trang',
    avatarColor: '#ed93b1',
    tag: 'Thảo luận',
    replies: 15,
    views: 388,
    time: '1 ngày trước',
    excerpt:
      'Mình chạy thử 200 request tóm tắt document trên cả hai model cùng độ dài input, kết quả chi phí và chất lượng đính kèm bảng bên dưới...',
    replyThread: [],
  },
  {
    id: 'f5',
    title: 'Repo mẫu: RAG pipeline với LlamaIndex + Qdrant',
    author: 'Nam Khánh',
    avatarColor: '#85b7eb',
    tag: 'Chia sẻ',
    replies: 9,
    views: 276,
    time: '1 ngày trước',
    excerpt:
      'Chia sẻ repo mình dùng để demo RAG pipeline cho bài tập tuần trước, có sẵn docker-compose để chạy Qdrant local...',
    replyThread: [],
  },
  {
    id: 'f6',
    title: 'Prompt injection và cách phòng tránh khi build AI agent',
    author: 'Bảo Trâm',
    avatarColor: '#fac775',
    tag: 'Bảo mật',
    replies: 18,
    views: 401,
    time: '2 ngày trước',
    excerpt:
      'Sau khi đọc paper mới về prompt injection, mình tổng hợp lại 5 kỹ thuật phòng tránh cơ bản khi build agent có quyền gọi tool...',
    replyThread: [],
  },
]
