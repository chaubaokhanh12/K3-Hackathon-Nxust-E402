import { Tag, Check } from './Icons.jsx'

const VARIANT = {
  resolved: { Icon: Check, color: 'text-[#3ba55d]' },
  tag: { Icon: Tag, color: 'text-dc-muted' },
}

export default function SystemMessage({ variant = 'tag', children }) {
  const { Icon, color } = VARIANT[variant] ?? VARIANT.tag
  return (
    <div className={`animate-fade-up flex items-center gap-2 px-4 py-1.5 text-[13px] ${color}`}>
      <Icon size={15} className="shrink-0" />
      <span>{children}</span>
    </div>
  )
}
