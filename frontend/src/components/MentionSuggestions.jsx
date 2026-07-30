import { At } from './Icons.jsx'

function initials(name) {
  return name.split(' ').slice(-2).map((w) => w[0]).join('').toUpperCase()
}

export default function MentionSuggestions({ options, activeIndex, onSelect, onHover }) {
  if (!options.length) return null

  return (
    <div className="absolute bottom-full left-0 right-0 z-20 mb-2 max-h-64 overflow-y-auto rounded-lg border border-dc-border bg-[#111214] p-1.5 shadow-lg">
      <div className="px-2 py-1 text-[11px] font-bold uppercase tracking-wide text-dc-muted">
        Thành viên khớp "@"
      </div>
      {options.map((m, i) => (
        <button
          key={m.id}
          type="button"
          onMouseDown={(e) => {
            e.preventDefault() // giữ focus input, tránh blur trước khi click được ghi nhận
            onSelect(m)
          }}
          onMouseEnter={() => onHover(i)}
          className={`flex w-full items-center gap-2 rounded px-2 py-1.5 text-left text-[14px] transition-colors ${
            i === activeIndex ? 'bg-dc-blurple text-white' : 'text-dc-text hover:bg-dc-hover'
          }`}
        >
          <span
            className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[10px] font-bold text-black/70"
            style={{ backgroundColor: m.color }}
          >
            {m.special ? <At size={13} /> : initials(m.name)}
          </span>
          <span className="truncate font-medium">{m.name}</span>
          <span className={`ml-auto shrink-0 truncate text-[11px] ${i === activeIndex ? 'text-white/80' : 'text-dc-muted'}`}>
            {m.role ?? m.hint ?? ''}
          </span>
        </button>
      ))}
    </div>
  )
}
