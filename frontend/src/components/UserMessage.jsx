import MentionText from './MentionText.jsx'
import { Reply } from './Icons.jsx'

const ROLE_STYLE = {
  LABCOACH: 'bg-[#1f3d2b] text-[#3ba55d]',
  ADMIN: 'bg-[#4a1b0c] text-[#f0997b]',
}

function initials(name) {
  return name
    .split(' ')
    .filter((w) => !/^(labcoach|admin)$/i.test(w))
    .slice(0, 2)
    .map((w) => w[0])
    .join('')
    .toUpperCase()
}

/** Dòng trích dẫn "đang trả lời" phía trên tin nhắn, giống reply-reference của Discord thật. */
function ReplyPreview({ replyTo }) {
  return (
    <div className="mb-0.5 ml-1 flex items-center gap-1.5 text-[13px] text-dc-muted">
      <Reply size={14} className="shrink-0 -scale-x-100" />
      <span
        className="h-4 w-4 shrink-0 rounded-full"
        style={{ backgroundColor: replyTo.avatarColor }}
      />
      <span className="font-medium text-dc-text">{replyTo.author}</span>
      <span className="truncate">{replyTo.body}</span>
    </div>
  )
}

export default function UserMessage({ author, avatarColor, role, time, body, replyTo, children }) {
  return (
    <div className="animate-fade-up px-4 py-2 hover:bg-[#2e3035]">
      {replyTo && (
        <div className="ml-[52px]">
          <ReplyPreview replyTo={replyTo} />
        </div>
      )}
      <div className="flex gap-4">
        <div
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-[13px] font-bold text-black/70"
          style={{ backgroundColor: avatarColor }}
        >
          {initials(author)}
        </div>
        <div className="min-w-0 flex-1">
          <div className="mb-0.5 flex items-center gap-2">
            <span className="text-[15px] font-semibold text-white">{author}</span>
            {role && (
              <span className={`rounded px-1.5 py-px text-[10px] font-bold uppercase leading-tight ${ROLE_STYLE[role] ?? ''}`}>
                {role}
              </span>
            )}
            <span className="text-[12px] text-dc-muted">{time}</span>
          </div>
          {body && <MentionText text={body} />}
          {children}
        </div>
      </div>
    </div>
  )
}
