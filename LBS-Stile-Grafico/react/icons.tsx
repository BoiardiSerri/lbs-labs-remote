/* Icone 16×16 monocromatiche in currentColor.
   plus, chevron_down, chevron_up, close, check: copiate dagli asset originali del design system (close e check senza colore fisso).
   Le altre sono disegnate nello stesso stile: tratto 1.4, terminali e giunzioni tonde. */
import type { CSSProperties, ReactNode } from 'react'

const S = { fill: 'none', stroke: 'currentColor', strokeWidth: 1.4, strokeLinecap: 'round', strokeLinejoin: 'round' } as const
const F = { fill: 'currentColor', stroke: 'none' } as const

const ICONS: Record<string, ReactNode> = {
  // ---- da design-export/assets ----
  plus: <path d="M8 3v10M3 8h10" {...S} strokeWidth={2} />,
  chevron_down: <path d="M3.5 6l4.5 4.5L12.5 6" {...S} strokeWidth={2} />,
  chevron_up: <path d="M3.5 10l4.5-4.5L12.5 10" {...S} strokeWidth={2} />,
  chevron_right: <path d="M6 3.5l4.5 4.5L6 12.5" {...S} strokeWidth={2} />,
  close: <path d="M4.5 4.5l7 7M11.5 4.5l-7 7" {...S} strokeWidth={1.6} />,
  check: <path d="M3.5 8.5l3 3 6-7" {...S} strokeWidth={2} />,
  // ---- trasporto ----
  play: <path d="M5 3.2v9.6L12.8 8z" {...F} />,
  pause: <path d="M4.5 3h2.4v10H4.5zM9.1 3h2.4v10H9.1z" {...F} />,
  step_back: <><path d="M12 3.5v9L6 8z" {...F} /><path d="M4 3.5v9" {...S} /></>,
  step_fwd: <><path d="M4 3.5v9L10 8z" {...F} /><path d="M12 3.5v9" {...S} /></>,
  to_start: <><path d="M3 3v10" {...S} /><path d="M9 4v8L5 8zM13.5 4v8l-4-4z" {...F} /></>,
  to_end: <><path d="M13 3v10" {...S} /><path d="M7 4v8l4-4zM2.5 4v8l4-4z" {...F} /></>,
  // ---- modifica ----
  scissors: <><circle cx="4.5" cy="11.5" r="2" {...S} /><circle cx="11.5" cy="11.5" r="2" {...S} /><path d="M5.8 10L12 2.5M10.2 10L4 2.5" {...S} /></>,
  split: <><rect x="1.5" y="6" width="13" height="5" rx="1.5" {...S} /><path d="M8 2v12" {...S} /><path d="M6.5 2h3" {...S} /></>,
  copy: <><rect x="5.5" y="5.5" width="8" height="8.5" rx="1.5" {...S} /><path d="M3.5 10.5h-.5a1 1 0 0 1-1-1V3a1 1 0 0 1 1-1h6.5a1 1 0 0 1 1 1v.5" {...S} /></>,
  paste: <><rect x="3" y="3.5" width="10" height="11" rx="1.5" {...S} /><path d="M6 3.5V2.5h4v1M6 8h4M6 11h3" {...S} /></>,
  trash: <><path d="M2.5 4.5h11M6 4.5V2.8h4v1.7M4 4.5l.7 9h6.6l.7-9" {...S} /><path d="M6.8 7v4.5M9.2 7v4.5" {...S} /></>,
  // ---- effetti ----
  fade: <><path d="M2 13L14 3v10z" {...S} /></>,
  crossfade: <><path d="M2 3l12 10M2 13L14 3" {...S} /><path d="M2 3v10M14 3v10" {...S} /></>,
  refresh: <path d="M13 8a5 5 0 1 1-1.5-3.6M13 2.5v3h-3" {...S} />,
  rec: <><circle cx="8" cy="8" r="6" {...S} /><circle cx="8" cy="8" r="3.6" fill="currentColor" /></>,
  stop: <rect x="4" y="4" width="8" height="8" rx="1.5" fill="currentColor" />,
  kenburns: <><rect x="1.5" y="3" width="13" height="10" rx="1.5" {...S} /><path d="M5 10.5l5-5M7 5.5h3v3" {...S} /></>,
  denoise: <><path d="M1.5 8h1.5l1.2-3.5L6 11.5 7.6 4 9.2 11l1.4-4.5 1.2 2.5h2.7" {...S} /><path d="M3 14L13 2" {...S} strokeWidth={0.9} /></>,
  // ---- strumenti ----
  magnet: <><path d="M3.5 2.5v5a4.5 4.5 0 0 0 9 0v-5" {...S} /><path d="M3.5 2.5h2.6v5a1.9 1.9 0 0 0 3.8 0v-5h2.6" {...S} /><path d="M3.5 5h2.6M9.9 5h2.6" {...S} /></>,
  mixer: <><path d="M4 2v12M8 2v12M12 2v12" {...S} /><rect x="2.5" y="8.5" width="3" height="2.4" rx=".8" {...F} /><rect x="6.5" y="4" width="3" height="2.4" rx=".8" {...F} /><rect x="10.5" y="10" width="3" height="2.4" rx=".8" {...F} /></>,
  title: <path d="M3 3.5h10M8 3.5v9.5M6 13h4" {...S} strokeWidth={1.6} />,
  sidebar: <><rect x="1.5" y="2.5" width="13" height="11" rx="1.5" {...S} /><path d="M6 2.5v11" {...S} /><path d="M3.3 5h1M3.3 7h1M3.3 9h1" {...S} /></>,
  sort: <><path d="M4.5 2.5v11M2.5 11.5l2 2 2-2" {...S} /><path d="M8.5 4h5M8.5 7.5h4M8.5 11h2.5" {...S} /></>,
  scenes: <><rect x="1.5" y="3.5" width="5.5" height="9" rx="1" {...S} /><rect x="9" y="3.5" width="5.5" height="9" rx="1" {...S} /><path d="M8 1.5v13" {...S} strokeDasharray="1.2 1.8" /></>,
  folder: <path d="M1.8 4.2a1 1 0 0 1 1-1h3.4l1.4 1.6h5.6a1 1 0 0 1 1 1v6.4a1 1 0 0 1-1 1H2.8a1 1 0 0 1-1-1z" {...S} />,
  // ---- tipi di media ----
  film: <><rect x="2" y="2" width="12" height="12" rx="1.5" {...S} /><path d="M5 2v12M11 2v12M2 5.5h3M2 10.5h3M11 5.5h3M11 10.5h3" {...S} /></>,
  wave: <path d="M1.5 8h1.2M4.2 5.5v5M6.6 3v10M9 5v6M11.4 6.5v3M13.8 8h.7" {...S} />,
  photo: <><rect x="1.5" y="2.5" width="13" height="11" rx="1.5" {...S} /><circle cx="5.5" cy="6" r="1.3" {...S} /><path d="M2 12l4-3.5 2.5 2 2.5-3 3.5 4" {...S} /></>,
  // ---- collegamenti e tracce ----
  link: <><path d="M6.5 9.5l3-3" {...S} /><path d="M7.5 4.3l1.3-1.3a2.6 2.6 0 0 1 3.7 3.7l-1.3 1.3M8.5 11.7l-1.3 1.3a2.6 2.6 0 0 1-3.7-3.7l1.3-1.3" {...S} /></>,
  unlink: <><path d="M7.5 4.3l1.3-1.3a2.6 2.6 0 0 1 3.7 3.7l-1.3 1.3M8.5 11.7l-1.3 1.3a2.6 2.6 0 0 1-3.7-3.7l1.3-1.3" {...S} /><path d="M2 2l2 2M12 12l2 2M5 1.5v1.5M11 13v1.5" {...S} /></>,
  eye: <><path d="M1.5 8s2.4-4.5 6.5-4.5S14.5 8 14.5 8s-2.4 4.5-6.5 4.5S1.5 8 1.5 8z" {...S} /><circle cx="8" cy="8" r="2" {...S} /></>,
  eye_off: <><path d="M1.5 8s2.4-4.5 6.5-4.5S14.5 8 14.5 8s-2.4 4.5-6.5 4.5S1.5 8 1.5 8z" {...S} /><path d="M2.5 13.5l11-11" {...S} /></>,
  speaker: <><path d="M2.5 6h2.5l3.5-3v10L5 10H2.5z" {...S} /><path d="M10.8 5.5a3.5 3.5 0 0 1 0 5M12.6 3.8a6 6 0 0 1 0 8.4" {...S} /></>,
  speaker_off: <><path d="M2.5 6h2.5l3.5-3v10L5 10H2.5z" {...S} /><path d="M10.5 6l4 4M14.5 6l-4 4" {...S} /></>,
  warning: <><path d="M8 2L14.5 13.5h-13z" {...S} /><path d="M8 6.3v3.4" {...S} /><circle cx="8" cy="11.6" r=".9" {...F} /></>,
  in_point: <path d="M10.5 3H6v10h4.5" {...S} strokeWidth={1.6} />,
  out_point: <path d="M5.5 3H10v10H5.5" {...S} strokeWidth={1.6} />
}

export type IconName = keyof typeof ICONS

export function Icon({ name, size = 16, className, style }: { name: IconName | string; size?: number; className?: string; style?: CSSProperties }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" className={className} style={style} aria-hidden="true" focusable="false">
      {ICONS[name] ?? null}
    </svg>
  )
}

export const iconNames = Object.keys(ICONS)

/** L'icona come immagine SVG (data URL) di un colore preciso: per disegnarla su canvas. */
export function iconDataUrl(name: string, color: string, renderToString: (n: ReactNode) => string): string {
  const body = renderToString(<g style={{ color }}>{ICONS[name]}</g>)
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" color="${color}">${body}</svg>`)}`
}
