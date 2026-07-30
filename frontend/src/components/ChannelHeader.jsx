import { Hash, MessageCircle, Trophy, Book, Bell, Pin, Users, Search, Inbox, Help, Tag } from './Icons.jsx'

const ICON_BY_KEY = {
  chat: MessageCircle,
  trophy: Trophy,
  book: Book,
  hash: Hash,
}

export default function ChannelHeader({ icon = 'hash', title, topic, resolved, showMembers, onToggleMembers }) {
  const Icon = ICON_BY_KEY[icon] ?? Hash

  return (
    <header className="flex h-12 shrink-0 items-center gap-3 border-b border-dc-divider px-4 shadow-[0_1px_0_rgba(0,0,0,0.2)]">
      <Icon size={22} className="text-dc-muted" />
      <h1 className="text-[15px] font-semibold text-white">{title}</h1>

      {resolved && (
        <span className="flex items-center gap-1 rounded bg-[#1f3d2b] px-2 py-0.5 text-[11px] font-bold uppercase tracking-wide text-[#3ba55d]">
          <Tag size={12} />
          Đã xử lý
        </span>
      )}

      {topic && (
        <>
          <div className="mx-1 h-6 w-px bg-dc-border" />
          <p className="hidden truncate text-[13px] text-dc-muted lg:block">{topic}</p>
        </>
      )}

      <div className="ml-auto flex items-center gap-4 text-dc-muted">
        <button className="hover:text-dc-text" aria-label="Thông báo"><Bell /></button>
        <button className="hover:text-dc-text" aria-label="Tin đã ghim"><Pin /></button>
        <button
          onClick={onToggleMembers}
          aria-label="Danh sách thành viên"
          className={showMembers ? 'text-white' : 'hover:text-dc-text'}
        >
          <Users />
        </button>
        <div className="flex h-6 items-center gap-1 rounded bg-dc-rail px-2">
          <input
            readOnly
            placeholder="Tìm kiếm"
            className="w-24 bg-transparent text-[13px] text-dc-text outline-none placeholder:text-dc-muted"
          />
          <Search size={14} />
        </div>
        <button className="hover:text-dc-text" aria-label="Hộp thư"><Inbox /></button>
        <button className="hover:text-dc-text" aria-label="Trợ giúp"><Help /></button>
      </div>
    </header>
  )
}
