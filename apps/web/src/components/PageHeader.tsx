export function PageHeader({ eyebrow, title, subtitle, right }: { eyebrow?: string; title: string; subtitle?: string; right?: React.ReactNode }) {
  return (
    <div className="px-10 pt-10 pb-6 border-b border-line">
      <div className="flex items-start justify-between">
        <div>
          {eyebrow && (
            <div className="font-mono text-[11px] uppercase tracking-widest text-mute mb-2">{eyebrow}</div>
          )}
          <h1 className="font-display text-4xl tracking-tight leading-tight">{title}</h1>
          {subtitle && <p className="text-mute-2 max-w-2xl mt-3 leading-relaxed">{subtitle}</p>}
        </div>
        {right}
      </div>
    </div>
  );
}

export function RagChip({ rag }: { rag: string }) {
  return <span className={`chip rag-${rag}`}>{rag}</span>;
}
