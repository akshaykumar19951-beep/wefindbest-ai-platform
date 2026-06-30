import Link from "next/link";

export default function Home() {
  return (
    <main className="min-h-screen bg-zinc-50 px-6 py-10 text-zinc-950">
      <div className="mx-auto flex max-w-4xl flex-col gap-8">
        <header className="flex items-center justify-between">
          <h1 className="text-xl font-semibold">WeFindBest AI</h1>
          <nav className="flex gap-2 text-sm">
            <Link className="rounded-md border border-zinc-300 px-3 py-2" href="/login">
              Login
            </Link>
            <Link className="rounded-md bg-zinc-950 px-3 py-2 text-white" href="/register">
              Register
            </Link>
          </nav>
        </header>

        <section className="rounded-md border border-zinc-200 bg-white p-8">
          <h2 className="text-3xl font-semibold tracking-tight">AI API SaaS starter</h2>
          <p className="mt-3 max-w-2xl text-zinc-600">
            Create an account, copy your API key, and test authenticated chat requests from the
            dashboard or Swagger.
          </p>
          <div className="mt-6 flex gap-3">
            <Link className="rounded-md bg-zinc-950 px-4 py-2 text-sm font-medium text-white" href="/dashboard">
              Open dashboard
            </Link>
            <Link className="rounded-md border border-zinc-300 px-4 py-2 text-sm font-medium" href="/register">
              Get API key
            </Link>
          </div>
        </section>
      </div>
    </main>
  );
}
