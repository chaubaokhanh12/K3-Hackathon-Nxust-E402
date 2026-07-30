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

export default function UserMessage({ author, avatarColor, role, time, body, children }) {
  return (
    <div className="animate-fade-up px-4 py-2 hover:bg-[#2e3035]">
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
          {body && <p className="whitespace-pre-wrap text-[15px] leading-relaxed text-dc-text">{body}</p>}
          {children}
        </div>
      </div>
    </div>
  )
}
