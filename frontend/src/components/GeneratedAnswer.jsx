import { Sparkles } from './Icons.jsx'

const CITATION = /\[#(\d+)\]/g

/**
 * Câu trả lời do LLM tổng hợp từ các thread lấy được.
 *
 * Backend đã bảo đảm mọi `[#thread_id]` trong text đều trỏ tới một thread có
 * thật trong `suggestions` (guardrail neo nguồn ở src/agent/synthesis.py).
 * Ở đây chỉ đổi id dài thành số thứ tự thẻ nguồn bên dưới cho dễ đọc.
 */
export default function GeneratedAnswer({ answer, suggestions = [] }) {
  if (!answer?.text) return null

  const rankByThreadId = new Map(
    suggestions.map((thread, index) => [String(thread.thread_id), thread.rank ?? index + 1]),
  )

  const parts = []
  let cursor = 0
  for (const match of answer.text.matchAll(CITATION)) {
    if (match.index > cursor) parts.push(answer.text.slice(cursor, match.index))
    const rank = rankByThreadId.get(match[1])
    // Không có rank = id lạ. Backend lẽ ra đã loại; bỏ nhãn thay vì hiện id thô.
    if (rank) {
      parts.push(
        <sup
          key={`${match.index}-${match[1]}`}
          title={`Nguồn: thread #${rank}`}
          className="mx-0.5 rounded bg-dc-blurple/25 px-1 py-px font-mono text-[10px] text-[#949cf0]"
        >
          {rank}
        </sup>,
      )
    }
    cursor = match.index + match[0].length
  }
  if (cursor < answer.text.length) parts.push(answer.text.slice(cursor))

  return (
    <div className="mt-3 rounded border border-dc-blurple/40 bg-[#35373c] p-3">
      <div className="mb-1.5 flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide text-[#949cf0]">
        <Sparkles size={13} />
        DupBot tổng hợp
      </div>
      <p className="whitespace-pre-wrap text-[14px] leading-relaxed text-dc-text">{parts}</p>
      <p className="mt-2 text-[11px] leading-relaxed text-dc-muted">
        Viết lại từ các thread bên dưới{answer.model ? ` bằng ${answer.model}` : ''}. Số nhỏ là
        nguồn — đọc thread gốc để chắc chắn.
      </p>
    </div>
  )
}
