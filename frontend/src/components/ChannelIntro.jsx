import { Hash } from './Icons.jsx'
import { THREADS } from '../data/threads.js'

export default function ChannelIntro() {
  return (
    <div className="px-4 pb-4 pt-8">
      <div className="mb-3 flex h-16 w-16 items-center justify-center rounded-full bg-dc-input">
        <Hash size={38} className="text-white" />
      </div>
      <h2 className="text-[28px] font-bold text-white">Chào mừng tới #hoi-dap</h2>
      <p className="mt-1 max-w-xl text-[15px] leading-relaxed text-dc-muted">
        Đây là nơi đặt câu hỏi về bài học, môi trường và logistics. Kênh đang có{' '}
        <strong className="font-semibold text-dc-text">{THREADS.length} thread đã có lời giải</strong> —
        DupBot tự đọc mỗi câu hỏi mới và chỉ ra thread cũ cùng vấn đề, kể cả khi bạn dùng từ khác.
      </p>
    </div>
  )
}
