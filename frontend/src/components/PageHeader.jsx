export default function PageHeader({ title, subtitle, children, testId }) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 mb-7" data-testid={testId}>
      <div>
        <h1 className="font-heading text-3xl sm:text-4xl font-bold tracking-tight text-white">{title}</h1>
        {subtitle && <p className="text-sm text-slate-400 mt-1.5 max-w-2xl">{subtitle}</p>}
      </div>
      {children && <div className="flex items-center gap-2.5">{children}</div>}
    </div>
  );
}
