import { MEMBERS } from '../data/threads.js'

const ROLE_COLOR = {
  LABCOACH: 'text-[#3ba55d]',
  ADMIN: 'text-[#f0997b]',
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

function Row({ member, offline }) {
  return (
    <div className={`flex items-center gap-2.5 rounded px-2 py-1 hover:bg-dc-hover ${offline ? 'opacity-40' : ''}`}>
      <div className="relative shrink-0">
        <div
          className="flex h-8 w-8 items-center justify-center rounded-full text-[11px] font-bold text-black/70"
          style={{ backgroundColor: member.color }}
        >
          {initials(member.name)}
        </div>
        <span
          className={`absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full border-[2.5px] border-dc-sidebar ${
            offline ? 'bg-dc-muted' : 'bg-dc-green'
          }`}
        />
      </div>
      <div className="min-w-0">
        <div className="flex items-center gap-1.5">
          <span className={`truncate text-[14px] font-medium ${ROLE_COLOR[member.role] ?? 'text-dc-text'}`}>
            {member.name}
          </span>
          {member.bot && (
            <span className="rounded bg-dc-blurple px-1 text-[9px] font-bold text-white">BOT</span>
          )}
        </div>
        {member.status && <div className="truncate text-[11px] text-dc-muted">{member.status}</div>}
      </div>
    </div>
  )
}

export default function MemberList() {
  return (
    <aside className="dc-scroll hidden w-60 shrink-0 overflow-y-auto bg-dc-sidebar px-2 py-4 xl:block">
      <div className="px-2 pb-1 text-[11px] font-bold uppercase tracking-wide text-dc-muted">
        Đang online — {MEMBERS.online.length}
      </div>
      {MEMBERS.online.map((m) => (
        <Row key={m.name} member={m} />
      ))}

      <div className="mt-4 px-2 pb-1 text-[11px] font-bold uppercase tracking-wide text-dc-muted">
        Offline — {MEMBERS.offline.length}
      </div>
      {MEMBERS.offline.map((m) => (
        <Row key={m.name} member={m} offline />
      ))}
    </aside>
  )
}
