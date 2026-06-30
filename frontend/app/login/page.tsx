"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { login } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      const data = await login(email, password);
      localStorage.setItem("wefindbest_access_token", data.access_token);
      localStorage.setItem("wefindbest_refresh_token", data.refresh_token);
      localStorage.setItem("wefindbest_api_key", data.api_key);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-zinc-50 px-6 text-zinc-950">
      <form className="w-full max-w-sm rounded-md border border-zinc-200 bg-white p-6" onSubmit={onSubmit}>
        <h1 className="text-2xl font-semibold">Login</h1>
        <div className="mt-6 space-y-4">
          <input
            className="w-full rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-900"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Email"
            required
          />
          <input
            className="w-full rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-900"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Password"
            required
          />
        </div>
        {error && <p className="mt-4 text-sm text-red-600">{error}</p>}
        <button
          className="mt-6 w-full rounded-md bg-zinc-950 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
          disabled={loading}
        >
          {loading ? "Logging in" : "Login"}
        </button>
        <p className="mt-4 text-sm text-zinc-600">
          No account? <Link className="font-medium text-zinc-950" href="/register">Register</Link>
        </p>
      </form>
    </main>
  );
}
