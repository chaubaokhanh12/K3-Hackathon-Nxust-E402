/** Data giả cho kênh chat thường #chung — không có bot, chỉ trò chuyện tự do. */

export const GENERAL_SEED = [
  { author: 'Gia Hân', avatarColor: '#5dcaa5', time: '10:12', body: 'Chào cả nhà, hôm nay mình mới join khoá 👋' },
  {
    author: 'Minh Đức',
    avatarColor: '#7f77dd',
    time: '10:13',
    body: 'Chào bạn! Đọc kênh #gioi-thieu trước nhé, có link lấy role theo lớp.',
    replyTo: { author: 'Gia Hân', avatarColor: '#5dcaa5', body: 'Chào cả nhà, hôm nay mình mới join khoá 👋' },
  },
  { author: 'Nam Khánh', avatarColor: '#85b7eb', time: '10:20', body: 'Có ai đang làm mini hackathon hướng Discord bot không, mình muốn trao đổi thêm' },
  {
    author: 'Bảo Trâm',
    avatarColor: '#fac775',
    time: '10:24',
    body: 'Nhóm mình đang làm hướng đó, qua #chia-se xem bài mình mới đăng nhé. @[Nam Khánh] thử tag xem có nhận thông báo không nè',
  },
]
