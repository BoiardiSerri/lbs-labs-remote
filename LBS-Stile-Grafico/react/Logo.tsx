/* Marchio LBS (Lucio Boiardi Serri): monocromatico come logo_rcf.svg,
   disco bianco con anello sottile e le tre lettere L B S nere, disegnate a tracciati (nessun font).
   I colori sono --color-text (disco) e --color-ink (segni). */
const BRAND = 'LBS Labs'

export function Logo({ size = 32, opacity = 1 }: { size?: number; opacity?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 134 134" aria-label={BRAND} role="img" style={{ opacity }}>
      <circle cx="67" cy="67" r="66.5" fill="var(--color-text)" />
      <circle cx="67" cy="67" r="61.5" fill="none" stroke="var(--color-ink)" strokeWidth="3.4" />
      <g fill="var(--color-ink)">
        {/* L */}
        <path d="M19 45h11v34h14v10H19z" />
        {/* B (con i due occhielli vuoti) */}
        <path fillRule="evenodd" d="M49 45h17c7.500 0 12 3.700 12 10 0 3.700-1.800 6.300-4.800 7.800 4 1.300 6.300 4.500 6.300 9 0 7-5 11.200-13 11.200H49zM60 54v7.500h5c2.800 0 4.200-1.300 4.200-3.800S67.800 54 65 54zM60 70v9.500h6c3 0 4.700-1.600 4.700-4.700S69 70 66 70z" />
      </g>
      {/* S (tracciato con tratto, per curve regolari) */}
      <path d="M115.500 55.500c-1.600-4.800-6-6.800-11-6.800-6 0-10.300 2.800-10.300 7.600 0 11 22.500 5.400 22.500 18.600 0 6-5 9.600-12 9.600-6 0-11-2.400-12.800-7.600" fill="none" stroke="var(--color-ink)" strokeWidth="9" />
    </svg>
  )
}
