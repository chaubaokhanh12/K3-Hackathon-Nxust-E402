import { Sparkles, Clock } from './Icons.jsx'

/**
 * Tin nhắn bot gửi khi học viên bấm "Chưa đúng ý tôi" hoặc khi không tìm thấy gì.
 * Điểm chính: LabCoach được tag kèm ngữ cảnh sẵn — câu hỏi gốc, thread đã loại,
 * và lý do vì sao gợi ý tự động không dùng được.
 */
export default function EscalationMessage({ query, rejected, reason }) {
  return (
    <div className="animate-fade-up px-4 py-2 hover:bg-[#2e3035]">
      <div className="flex gap-4">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-dc-blurple text-white">
          <Sparkles size={20} />
        </div>
        <div className="min-w-0 flex-1">
          <div className="mb-1 flex items-center gap-2">
            <span className="text-[15px] font-semibold text-[#949cf0]">DupBot</span>
            <span className="rounded bg-dc-blurple px-1 py-px text-[10px] font-bold leading-tight text-white">BOT</span>
            <span className="text-[12px] text-dc-muted">vừa xong</span>
          </div>

          <div className="max-w-2xl rounded border-l-[4px] border-dc-yellow bg-[#2b2d31] p-3">
            <p className="text-[15px] leading-relaxed text-dc-text">
              <span className="rounded bg-dc-mention px-1 py-0.5 font-medium text-[#c9cdfb]">@LabCoach</span>{' '}
              câu hỏi này cần người thật. Ngữ cảnh đã tổng hợp sẵn để bạn không phải đọc lại từ đầu.
            </p>

            <dl className="mt-3 space-y-2 text-[14px]">
              <div>
                <dt className="text-[12px] font-bold uppercase tracking-wide text-dc-muted">Câu hỏi</dt>
                <dd className="mt-0.5 text-dc-text">{query}</dd>
              </div>

              <div>
                <dt className="text-[12px] font-bold uppercase tracking-wide text-dc-muted">Vì sao tự động không xử lý được</dt>
                <dd className="mt-0.5 text-dc-text">{reason}</dd>
              </div>

              {rejected.length > 0 && (
                <div>
                  <dt className="text-[12px] font-bold uppercase tracking-wide text-dc-muted">
                    Thread liên quan học viên đã xem và loại
                  </dt>
                  <dd className="mt-1 space-y-1">
                    {rejected.map((t) => (
                      <div key={t.thread_id ?? t.id} className="flex items-baseline gap-2 text-[13px]">
                        <span className="shrink-0 font-mono text-[11px] text-dc-muted">{t.similarity}%</span>
                        <a
                          href={t.thread_url ?? t.url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-dc-link hover:underline"
                        >
                          {t.thread_id ?? t.id} — {t.title}
                        </a>
                      </div>
                    ))}
                  </dd>
                </div>
              )}
            </dl>

            <div className="mt-3 flex items-center gap-2 border-t border-dc-border pt-2.5 text-[12px] text-dc-muted">
              <Clock size={14} />
              Thread gắn nhãn “Chờ LabCoach” · SLA phản hồi 25 phút
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
