export function PageHeader({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="mb-8 flex flex-col justify-between gap-4 border-b border-study-line pb-6 md:flex-row md:items-end">
      <div>
        {eyebrow ? <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-study-accent">{eyebrow}</p> : null}
        <h2 className="text-3xl font-semibold text-study-navy">{title}</h2>
        {description ? <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">{description}</p> : null}
      </div>
      {action}
    </div>
  );
}
