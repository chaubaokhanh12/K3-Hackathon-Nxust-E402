/**
 * Danh sách kênh trong sidebar — khớp cấu trúc server Discord thật của khoá.
 * `kind` quyết định App.jsx render component nào cho kênh đó:
 *   qa          #hoi-dap — DupBot, đã build đầy đủ
 *   chat        chat thường, không có bot
 *   forum       kênh dạng forum (mỗi tin là 1 post có tiêu đề riêng)
 *   info        kênh thông báo, học viên không đăng được
 *   placeholder kênh có thật ngoài đời nhưng chưa nằm trong lát cắt prototype
 */

export const CHANNEL_GROUPS = [
  {
    name: 'Cộng đồng',
    channels: [
      { id: 'chung', label: 'chung', icon: 'chat', kind: 'chat', topic: 'Trò chuyện chung, không liên quan bài học' },
      { id: 'hoi-dap', label: 'hoi-dap', icon: 'trophy', kind: 'qa', badge: 1, topic: 'Đặt câu hỏi về bài học, môi trường, deadline' },
      { id: 'chia-se', label: 'chia-se', icon: 'trophy', kind: 'forum', badge: 30, topic: 'Chia sẻ tips, tool, tin tức AI' },
      { id: 'bai-hoc', label: 'bai-hoc', icon: 'book', kind: 'info', badge: 5, topic: 'Thông báo bài học — chỉ giảng viên đăng' },
    ],
  },
  {
    name: 'Thông tin khoá',
    channels: [
      { id: 'gioi-thieu', label: 'gioi-thieu', icon: 'hash', kind: 'placeholder' },
      { id: 'thong-bao', label: 'thong-bao', icon: 'hash', kind: 'placeholder' },
      { id: 'lich-hoc', label: 'lich-hoc', icon: 'hash', kind: 'placeholder' },
      { id: 'bai-tap', label: 'bai-tap', icon: 'hash', kind: 'placeholder' },
    ],
  },
  {
    name: 'Mini Hackathon',
    channels: [
      { id: 'nhom-nxust', label: 'nhom-nxust', icon: 'hash', kind: 'placeholder' },
      { id: 'demo-day', label: 'demo-day', icon: 'hash', kind: 'placeholder' },
    ],
  },
]

export const ALL_CHANNELS = CHANNEL_GROUPS.flatMap((g) => g.channels)

export function getChannel(id) {
  return ALL_CHANNELS.find((c) => c.id === id)
}
