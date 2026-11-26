import { forwardRef, useEffect, useRef, type ButtonHTMLAttributes, type CSSProperties, type InputHTMLAttributes, type ReactNode } from 'react'
import { Icon, type IconName } from './icons'
// testi dell'interfaccia: sostituisci con il sistema di traduzioni del tuo programma
const t = (s: string) => s

const cx = (...c: (string | false | null | undefined)[]) => c.filter(Boolean).join(' ')

/* ---------------- Pannello con viti (STILE_LBS) ---------------- */
export interface PanelProps {
  title?: ReactNode
  headRight?: ReactNode
  screws?: boolean
  notch?: 'left' | 'right'
  qss?: boolean
  className?: string
  bodyClassName?: string
  style?: CSSProperties
  children?: ReactNode
}
export function Panel({ title, headRight, screws = true, notch, qss, className, bodyClassName, style, children }: PanelProps) {
  return (
    <section className={cx('ds-panel', qss && 'ds-panel--qss', className)} style={style}>
      {title !== undefined && (
        <header className="ds-panel__head">
          <div className="ds-panel__title t-heading">{title}</div>
          {headRight}
        </header>
      )}
      <div className={cx('ds-panel__body', title !== undefined && 'ds-panel__body--head', !screws && 'ds-panel__body--noscrews', bodyClassName)}>{children}</div>
      {notch && <div className={`ds-notch ds-notch--${notch}`} aria-hidden="true" />}
      {screws && <Screws />}
    </section>
  )
}
export function Screws() {
  return (
    <>
      <span className="ds-screw ds-screw--tl" aria-hidden="true" />
      <span className="ds-screw ds-screw--tr" aria-hidden="true" />
      <span className="ds-screw ds-screw--bl" aria-hidden="true" />
      <span className="ds-screw ds-screw--br" aria-hidden="true" />
    </>
  )
}

/* ---------------- Display incassato (STILE_LBS) ---------------- */
export function Display({ className, style, pad, children, ...rest }: { className?: string; style?: CSSProperties; pad?: boolean; children?: ReactNode } & Omit<React.HTMLAttributes<HTMLDivElement>, 'className' | 'style' | 'children'>) {
  return (
    <div className={cx('ds-display', pad && 'ds-display--pad', className)} style={style} {...rest}>
      {children}
    </div>
  )
}

/* ---------------- Pulsante a pillola (STILE_LBS) ---------------- */
export interface ButtonProps extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'title'> {
  variant?: 'normal' | 'primary' | 'ghost' | 'mute'
  small?: boolean
  checked?: boolean
  pending?: boolean
  icon?: IconName
  iconOnly?: boolean
  /** tooltip con nome e scorciatoia, es. "Dividi alla testina (S)" */
  tip?: string
}
export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = 'normal', small, checked, pending, icon, iconOnly, tip, className, children, type = 'button', ...rest },
  ref
) {
  return (
    <button
      ref={ref}
      type={type}
      className={cx('ds-btn', variant !== 'normal' && `ds-btn--${variant}`, small && 'ds-btn--small', iconOnly && 'ds-btn--icon', checked && 'is-checked', pending && 'is-pending', className)}
      data-tip={tip}
      aria-label={iconOnly ? tip : undefined}
      aria-pressed={checked === undefined ? undefined : checked}
      {...rest}
      // il clic col mouse non sposta il focus sul pulsante: così Spazio resta play/pausa e non lo ripreme
      onMouseDown={(e) => {
        e.preventDefault()
        rest.onMouseDown?.(e)
      }}
    >
      {icon && <Icon name={icon} className="ds-btn__icon" />}
      {!iconOnly && children !== undefined && <span className="ds-btn__label">{children}</span>}
    </button>
  )
})

/* ---------------- Segmentato (STILE_LBS) ---------------- */
export interface SegmentOption<T extends string> {
  value: T
  label: ReactNode
  count?: number
  disabled?: boolean
  tip?: string
}
export function Segmented<T extends string>({ options, value, onChange, full, small, disabled, ariaLabel }: {
  options: SegmentOption<T>[]
  value: T | null
  onChange?: (v: T) => void
  full?: boolean
  small?: boolean
  disabled?: boolean
  ariaLabel?: string
}) {
  return (
    <div className={cx('ds-seg', full && 'ds-seg--full', small && 'ds-seg--small')} role="radiogroup" aria-label={ariaLabel}>
      {options.map((o) => (
        <button
          key={o.value}
          type="button"
          role="radio"
          aria-checked={value === o.value}
          className={cx('ds-seg__item', value === o.value && 'is-checked')}
          disabled={disabled || o.disabled}
          data-tip={o.tip}
          onClick={() => onChange?.(o.value)}
        >
          {o.label}
          {o.count !== undefined && <span className="ds-seg__count">{o.count}</span>}
        </button>
      ))}
    </div>
  )
}

/* ---------------- Interruttore a pillola (STILE_LBS) ---------------- */
export function Toggle({ checked, onChange, disabled, children }: { checked: boolean; onChange?: (v: boolean) => void; disabled?: boolean; children?: ReactNode }) {
  const track = disabled ? 'var(--color-button-disabled)' : checked ? 'var(--color-accent)' : 'var(--color-bg-0)'
  const knob = disabled ? 'var(--color-text-disabled)' : checked ? 'var(--color-on-accent)' : 'var(--color-text-muted)'
  const stroke = checked ? 'var(--color-accent-bottom)' : 'var(--color-edge-field-top)'
  return (
    <label
      className={cx('ds-toggle', disabled && 'is-disabled')}
      tabIndex={disabled ? -1 : 0}
      role="switch"
      aria-checked={checked}
      aria-disabled={disabled}
      onClick={(e) => {
        e.preventDefault()
        if (!disabled) onChange?.(!checked)
      }}
      onKeyDown={(e) => {
        if (!disabled && (e.key === ' ' || e.key === 'Enter')) {
          e.preventDefault()
          onChange?.(!checked)
        }
      }}
    >
      <svg className="ds-toggle__track" width="30" height="16" viewBox="0 0 30 16">
        <rect x="0.5" y="0.5" width="29" height="15" rx="7.5" fill={track} stroke={stroke} />
        <circle cx={checked ? 22 : 8} cy="8" r="5" fill={knob} />
      </svg>
      {children && <span>{children}</span>}
    </label>
  )
}

/* ---------------- Campi (STILE_LBS) ---------------- */
export const Field = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement> & { numeric?: boolean }>(function Field({ numeric, className, ...rest }, ref) {
  return <input ref={ref} className={cx('ds-field', numeric && 'ds-field--num', className)} spellCheck={false} {...rest} />
})

export function SearchField({ value, onChange, placeholder, style }: { value: string; onChange: (v: string) => void; placeholder?: string; style?: CSSProperties }) {
  return (
    <div className="ds-search" style={style}>
      <Field value={value} placeholder={placeholder} onChange={(e) => onChange(e.target.value)} onKeyDown={(e) => e.key === 'Escape' && onChange('')} />
      {value && (
        <button type="button" className="ds-search__clear" aria-label={t('Svuota la ricerca')} onClick={() => onChange('')}>
          <Icon name="close" size={12} />
        </button>
      )}
    </div>
  )
}

/* ---------------- Slider (STILE_LBS) ---------------- */
export function Slider({ value, min, max, step = 1, onChange, disabled, width = 120, ariaLabel }: {
  value: number
  min: number
  max: number
  step?: number
  onChange?: (v: number) => void
  disabled?: boolean
  width?: number
  ariaLabel?: string
}) {
  return (
    <input
      type="range"
      className="ds-slider"
      style={{ width }}
      value={value}
      min={min}
      max={max}
      step={step}
      disabled={disabled}
      aria-label={ariaLabel}
      onChange={(e) => onChange?.(Number(e.target.value))}
    />
  )
}

/* ---------------- Chip di stato (STILE_LBS) ---------------- */
export type ChipStatus = 'ok' | 'warn' | 'error' | 'busy' | 'idle'
export function Chip({ status, children, size = 'bar', tip, onClick }: { status: ChipStatus; children: ReactNode; size?: 'bar' | 'small' | 'mini'; tip?: string; onClick?: () => void }) {
  const cls = cx('ds-chip', `ds-chip--${status}`, size === 'small' && 'ds-chip--small', size === 'mini' && 'ds-chip--mini')
  const text = <span className="ds-chip__text">{children}</span>
  return onClick ? (
    <button type="button" className={cls} data-tip={tip} onClick={onClick}>
      {text}
    </button>
  ) : (
    <span className={cls} data-tip={tip}>
      {text}
    </span>
  )
}

/* ---------------- Banner (STILE_LBS) ---------------- */
export function Banner({ kind, children, actions, onClose, style }: { kind: 'info' | 'warn'; children: ReactNode; actions?: ReactNode; onClose?: () => void; style?: CSSProperties }) {
  return (
    <div className={`ds-banner ds-banner--${kind}`} role={kind === 'warn' ? 'alert' : 'status'} style={style}>
      <div className="ds-banner__text">{children}</div>
      {(actions || onClose) && (
        <div className="ds-banner__actions">
          {actions}
          {onClose && <Button variant="ghost" small iconOnly icon="close" tip={t('Chiudi')} onClick={onClose} />}
        </div>
      )}
    </div>
  )
}

/* ---------------- Barra I/O (STILE_LBS) ---------------- */
export function IoBar({ left, right }: { left?: ReactNode; right?: ReactNode }) {
  const ref = useRef<HTMLCanvasElement>(null)
  useEffect(() => {
    const c = ref.current!
    const paint = () => {
      const dpr = window.devicePixelRatio || 1
      const W = c.clientWidth
      const H = c.clientHeight
      c.width = Math.round(W * dpr)
      c.height = Math.round(H * dpr)
      const x = c.getContext('2d')!
      x.setTransform(dpr, 0, 0, dpr, 0, 0)
      const css = getComputedStyle(c)
      const v = (n: string) => css.getPropertyValue(`--color-${n}`).trim()
      x.fillStyle = v('bg-io-bar')
      x.fillRect(0, 0, W, H)
      x.lineWidth = 1
      x.strokeStyle = v('edge-lo')
      x.beginPath(); x.moveTo(0, 0.5); x.lineTo(W, 0.5); x.stroke()
      x.strokeStyle = v('edge-hi')
      x.beginPath(); x.moveTo(0, 1.5); x.lineTo(W, 1.5); x.stroke()
      // due fasce a righe oblique ambra α115 al 30% e al 70%
      for (const at of [0.3, 0.7]) {
        const sx = W * at, t = 2, b = H, sw = 70
        x.save()
        x.beginPath(); x.moveTo(sx + sw * 0.3, t); x.lineTo(sx + sw, t); x.lineTo(sx + sw * 0.7, b); x.lineTo(sx, b); x.closePath(); x.clip()
        x.strokeStyle = v('accent')
        x.globalAlpha = 115 / 255
        x.lineWidth = 2
        const shift = (b - t) / Math.tan((60 * Math.PI) / 180)
        for (let p = sx - shift; p < sx + sw + shift; p += 9) { x.beginPath(); x.moveTo(p, b); x.lineTo(p + shift, t); x.stroke() }
        x.restore()
      }
    }
    paint()
    const ro = new ResizeObserver(paint)
    ro.observe(c)
    return () => ro.disconnect()
  }, [])
  return (
    <footer className="ds-iobar">
      <canvas ref={ref} aria-hidden="true" />
      <div className="ds-iobar__content">
        <div className="ds-iobar__msg">{left}</div>
        {right}
      </div>
    </footer>
  )
}
