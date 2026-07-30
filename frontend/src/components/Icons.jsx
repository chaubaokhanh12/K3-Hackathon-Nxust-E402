/** Icon SVG tối giản, stroke-based cho khớp bộ icon Discord. */

const base = {
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 2,
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
}

function Svg({ size = 20, children, ...rest }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" {...base} {...rest}>
      {children}
    </svg>
  )
}

export const Hash = (p) => (
  <Svg {...p}>
    <path d="M5 9h14M4 15h14M10 3L8 21M16 3l-2 18" />
  </Svg>
)

export const Bell = (p) => (
  <Svg {...p}>
    <path d="M18 8a6 6 0 1 0-12 0c0 7-3 8-3 8h18s-3-1-3-8M13.7 21a2 2 0 0 1-3.4 0" />
  </Svg>
)

export const Pin = (p) => (
  <Svg {...p}>
    <path d="M12 17v5M9 10.8V4h6v6.8l2 3.2H7l2-3.2Z" />
  </Svg>
)

export const Users = (p) => (
  <Svg {...p}>
    <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8M22 21v-2a4 4 0 0 0-3-3.9M16 3.1a4 4 0 0 1 0 7.8" />
  </Svg>
)

export const Search = (p) => (
  <Svg {...p}>
    <circle cx="11" cy="11" r="7" />
    <path d="m21 21-4.3-4.3" />
  </Svg>
)

export const Inbox = (p) => (
  <Svg {...p}>
    <path d="M22 12h-6l-2 3h-4l-2-3H2" />
    <path d="M5.5 5.1 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.5-6.9A2 2 0 0 0 16.8 4H7.2a2 2 0 0 0-1.7 1.1Z" />
  </Svg>
)

export const Help = (p) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="9" />
    <path d="M9.1 9a3 3 0 0 1 5.8 1c0 2-3 3-3 3M12 17h.01" />
  </Svg>
)

export const PlusCircle = (p) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 8v8M8 12h8" />
  </Svg>
)

export const Gift = (p) => (
  <Svg {...p}>
    <path d="M20 12v9H4v-9M2 7h20v5H2zM12 21V7M12 7H7.5a2.5 2.5 0 0 1 0-5C11 2 12 7 12 7ZM12 7h4.5a2.5 2.5 0 0 0 0-5C13 2 12 7 12 7Z" />
  </Svg>
)

export const Emoji = (p) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="9" />
    <path d="M8.5 14.5s1.2 1.8 3.5 1.8 3.5-1.8 3.5-1.8M9 9.5h.01M15 9.5h.01" />
  </Svg>
)

export const Sparkles = (p) => (
  <Svg {...p}>
    <path d="M12 3l1.7 4.8L18.5 9.5l-4.8 1.7L12 16l-1.7-4.8L5.5 9.5l4.8-1.7L12 3ZM18.5 16.5l.7 2 2 .7-2 .7-.7 2-.7-2-2-.7 2-.7.7-2Z" />
  </Svg>
)

export const Check = (p) => (
  <Svg {...p}>
    <path d="m4 12.5 5.5 5.5L20 7" />
  </Svg>
)

export const ThumbsDown = (p) => (
  <Svg {...p}>
    <path d="M17 14V3M6 14h8.4a2 2 0 0 0 2-1.6l1.2-6A2 2 0 0 0 15.6 4H8.5L6 14ZM6 14H4a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1h2v10Z" transform="rotate(180 12 12)" />
  </Svg>
)

export const ArrowRight = (p) => (
  <Svg {...p}>
    <path d="M5 12h14M13 6l6 6-6 6" />
  </Svg>
)

export const Reply = (p) => (
  <Svg {...p}>
    <path d="M9 17l-5-5 5-5M4 12h11a5 5 0 0 1 5 5v2" />
  </Svg>
)

export const Clock = (p) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 7v5l3.5 2" />
  </Svg>
)

export const Tag = (p) => (
  <Svg {...p}>
    <path d="M20.6 13.4 13.4 20.6a2 2 0 0 1-2.8 0l-7.2-7.2a2 2 0 0 1-.6-1.4V4a1 1 0 0 1 1-1h8a2 2 0 0 1 1.4.6l7.4 7.4a2 2 0 0 1 0 2.8Z" />
    <path d="M7.5 7.5h.01" />
  </Svg>
)

export const MessageCircle = (p) => (
  <Svg {...p}>
    <path d="M21 12a8 8 0 1 1-3.5-6.6M21 12l-4-1 1-4" />
    <path d="M8 12h.01M12 12h.01M16 12h.01" />
  </Svg>
)

export const Trophy = (p) => (
  <Svg {...p}>
    <path d="M8 21h8M12 17v4M7 4h10v5a5 5 0 0 1-10 0V4Z" />
    <path d="M7 5H4a1 1 0 0 0-1 1 5 5 0 0 0 4 4.9M17 5h3a1 1 0 0 1 1 1 5 5 0 0 1-4 4.9" />
  </Svg>
)

export const Book = (p) => (
  <Svg {...p}>
    <path d="M4 5a2 2 0 0 1 2-2h12v16H6a2 2 0 0 0-2 2V5Z" />
    <path d="M18 19H6a2 2 0 0 0 0 4h12" />
  </Svg>
)

export const MessageSquare = (p) => (
  <Svg {...p}>
    <path d="M4 4h16v12H8l-4 4V4Z" />
  </Svg>
)

export const Plus = (p) => (
  <Svg {...p}>
    <path d="M12 5v14M5 12h14" />
  </Svg>
)
