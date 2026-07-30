import { parseMentionSegments } from '../lib/mentions.js'

/** Render text thường + mention pill (giống @tag highlight của Discord). */
export default function MentionText({ text, className = '' }) {
  const segments = parseMentionSegments(text)

  return (
    <p className={`whitespace-pre-wrap text-[15px] leading-relaxed text-dc-text ${className}`}>
      {segments.map((seg, i) =>
        seg.type === 'mention' ? (
          <span key={i} className="rounded bg-dc-mention px-1 py-0.5 font-medium text-[#c9cdfb]">
            @{seg.value}
          </span>
        ) : (
          <span key={i}>{seg.value}</span>
        )
      )}
    </p>
  )
}
