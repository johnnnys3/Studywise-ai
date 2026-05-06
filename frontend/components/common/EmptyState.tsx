import Link from "next/link";

export function EmptyState({ title, description, href, actionLabel }: { title: string; description: string; href?: string; actionLabel?: string }) {
  return (
    <div className="rounded-lg border border-dashed border-slate-300 bg-white p-6 text-center sm:p-10">
      <h3 className="text-lg font-semibold text-study-navy">{title}</h3>
      <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-600">{description}</p>
      {href && actionLabel ? (
        <Link href={href} className="mt-5 inline-flex w-full justify-center rounded bg-study-navy px-4 py-2 text-sm font-semibold text-white hover:bg-black sm:w-auto">
          {actionLabel}
        </Link>
      ) : null}
    </div>
  );
}
