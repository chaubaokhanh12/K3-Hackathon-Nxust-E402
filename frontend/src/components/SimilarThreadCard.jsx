import { Reply, Check, ArrowRight } from './Icons.jsx'

/** Màu thanh similarity theo độ chắc chắn — cùng thang với confidence của bot. */
function barColor(similarity) {
  if (similarity >= 85) return 'bg-dc-green'
  if (similarity >= 78) return 'bg-[#3ba55d]'
  return 'bg-dc-yellow'
}

export default function SimilarThreadCard({ thread, rank }) {
  const id = thread.thread_id ?? thread.id
  const url = thread.thread_url ?? thread.url
  const isTopicOnly = thread.relevance === 'topic'
  const isVerified = thread.source_tier === 'VERIFIED'
  const answeredBy = thread.author_name ?? thread.answeredBy
  const replies = thread.replies
  const answeredAt = thread.answered_at ?? thread.answeredAt

  return (
    <article className="rounded border-l-[3px] border-dc-blurple bg-[#2b2d31] p-3">
      <div className="mb-1.5 flex items-start gap-2">
        <span className="mt-[3px] shrink-0 rounded bg-dc-rail px-1.5 py-0.5 font-mono text-[10px] text-dc-muted">
          #{rank}
        </span>
        <a
          href={url}
          target="_blank"
          rel="noreferrer"
          className="text-[14px] font-semibold leading-snug text-dc-link hover:underline"
        >
          {thread.title}
        </a>
      </div>

      <div className="mb-2 flex items-center gap-2">
        <div className="h-1 w-20 overflow-hidden rounded-full bg-dc-rail">
          <div className={`h-full rounded-full ${barColor(thread.similarity)}`} style={{ width: `${thread.similarity}%` }} />
        </div>
        <span className="font-mono text-[11px] text-dc-muted">{thread.similarity}% giống nghĩa</span>
      </div>

      {isTopicOnly ? (
        <p className="mb-2 text-[13px] leading-relaxed text-dc-yellow">
          Cùng chủ đề để tham khảo — chưa được dùng như lời giải trực tiếp.
        </p>
      ) : (
        <blockquote className="mb-2 border-l-2 border-dc-border pl-2.5 text-[14px] leading-relaxed text-dc-text">
          {thread.excerpt}
        </blockquote>
      )}

      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[12px] text-dc-muted">
        <span className={`flex items-center gap-1 ${isVerified ? 'text-[#3ba55d]' : 'text-dc-yellow'}`}>
          <Check size={13} /> {isVerified ? 'Đã xác minh' : 'Cộng đồng · chưa xác minh'}
        </span>
        {answeredBy && <span>{answeredBy}{thread.author_role ? ` · ${thread.author_role}` : ''}</span>}
        {replies != null && (
          <span className="flex items-center gap-1">
            <Reply size={13} /> {replies} trả lời
          </span>
        )}
        {answeredAt && <span>{answeredAt}</span>}
        <a
          href={url}
          target="_blank"
          rel="noreferrer"
          className="ml-auto flex items-center gap-1 text-dc-link hover:underline"
        >
          Mở thread {id} <ArrowRight size={13} />
        </a>
      </div>
    </article>
  )
}
