import SimilarThreadCard from './SimilarThreadCard.jsx'
import { Sparkles, Check, ThumbsDown, Clock } from './Icons.jsx'
import { CONFIDENCE } from '../lib/semanticSearch.js'

const COPY = {
  [CONFIDENCE.HIGH]: {
    headline: 'Mình tìm thấy câu hỏi tương tự đã có lời giải',
    note: 'Đọc trước ba thread này, phần lớn trường hợp là cùng một nguyên nhân.',
  },
  [CONFIDENCE.LOW]: {
    headline: 'Mình chỉ tìm được kết quả gần đúng',
    note: 'Độ khớp không cao nên có thể không đúng ý bạn. Nếu không giải quyết được, bấm nút bên dưới để mình gọi LabCoach.',
  },
  [CONFIDENCE.NONE]: {
    headline: 'Chưa có thread nào tương tự trong lịch sử kênh',
    note: 'Đây là câu hỏi mới. Mình đã chuyển trực tiếp cho LabCoach, bạn không cần làm gì thêm.',
  },
}

function BotAvatar() {
  return (
    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-dc-blurple text-white">
      <Sparkles size={20} />
    </div>
  )
}

export default function BotMessage({ result, status, onResolve, onEscalate }) {
  const { confidence, matches } = result
  const copy = COPY[confidence]
  const isNone = confidence === CONFIDENCE.NONE

  return (
    <div className="animate-fade-up px-4 py-2 hover:bg-[#2e3035]">
      <div className="flex gap-4">
        <BotAvatar />
        <div className="min-w-0 flex-1">
          <div className="mb-1 flex items-center gap-2">
            <span className="text-[15px] font-semibold text-[#949cf0]">DupBot</span>
            <span className="rounded bg-dc-blurple px-1 py-px text-[10px] font-bold leading-tight text-white">
              BOT
            </span>
            <span className="text-[12px] text-dc-muted">Hôm nay lúc {new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })}</span>
          </div>

          <div className="max-w-2xl rounded border-l-[4px] border-dc-blurple bg-[#2b2d31] p-3">
            <p className="text-[15px] font-semibold text-white">{copy.headline}</p>
            <p className="mt-0.5 text-[14px] leading-relaxed text-dc-muted">{copy.note}</p>

            {!isNone && (
              <>
                <div className="mt-3 space-y-2">
                  {matches.map((t, i) => (
                    <SimilarThreadCard key={t.id} thread={t} rank={i + 1} />
                  ))}
                </div>
                <p className="mt-2.5 text-[12px] leading-relaxed text-dc-muted">
                  Cách mình tìm: so ngữ nghĩa câu hỏi của bạn với {' '}
                  <span className="font-mono text-dc-text">toàn bộ thread đã giải</span> bằng embedding,
                  không so từ khoá — nên cách bạn diễn đạt khác vẫn khớp.
                </p>
              </>
            )}

            {status === 'pending' && (
              <div className="mt-3 flex flex-wrap gap-2 border-t border-dc-border pt-3">
                <button
                  onClick={onResolve}
                  className="flex items-center gap-1.5 rounded bg-dc-green px-3 py-1.5 text-[14px] font-medium text-white transition-colors hover:bg-[#1a8046]"
                >
                  <Check size={16} /> Đã giải quyết được
                </button>
                <button
                  onClick={onEscalate}
                  className="flex items-center gap-1.5 rounded border border-dc-border bg-transparent px-3 py-1.5 text-[14px] font-medium text-dc-text transition-colors hover:border-dc-muted hover:bg-dc-hover"
                >
                  <ThumbsDown size={16} /> Chưa đúng ý tôi
                </button>
              </div>
            )}

            {status === 'resolved' && (
              <div className="mt-3 flex items-center gap-2 border-t border-dc-border pt-3 text-[13px] text-[#3ba55d]">
                <Check size={16} />
                Bạn đã đánh dấu giải quyết được — thread gắn nhãn “Đã xử lý”, LabCoach không cần vào.
              </div>
            )}

            {status === 'escalated' && (
              <div className="mt-3 flex items-center gap-2 border-t border-dc-border pt-3 text-[13px] text-dc-yellow">
                <Clock size={16} />
                Đã chuyển LabCoach kèm ngữ cảnh. Thời gian phản hồi trung bình 25 phút.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
