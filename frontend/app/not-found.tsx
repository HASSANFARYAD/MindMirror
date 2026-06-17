import Link from "next/link";

export default function NotFound() {
  return (
    <div className="page-shell flex min-h-[70vh] items-center justify-center px-6">
      <div className="surface-card surface-card-hover w-full max-w-lg rounded-3xl p-8 text-center">
        <h1 className="text-3xl font-semibold text-mindmirror-primary">Page not found</h1>
        <p className="mt-3 text-sm leading-6 text-mindmirror-secondary">
          The page you requested does not exist or has moved.
        </p>
        <Link
          href="/journal"
          className="mt-6 inline-flex items-center justify-center rounded-full bg-[linear-gradient(135deg,#7C3AED_0%,#A855F7_100%)] px-5 py-3 text-sm font-semibold text-mindmirror-primary transition duration-[180ms] ease-out hover:shadow-[0_0_20px_rgba(139,92,246,0.4)]"
        >
          Go to Journal
        </Link>
      </div>
    </div>
  );
}
