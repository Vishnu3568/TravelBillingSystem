import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { dashboardPathForRole } from "../utils/routes.js";

export default function LoginPage() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [form, setForm] = useState({ username: "", password: "" });
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      const auth = await login(form);
      navigate(dashboardPathForRole(auth.role), { replace: true });
    } catch (loginError) {
      setError("Invalid username or password");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-100 text-slate-950">
      <div className="grid min-h-screen lg:grid-cols-[1.05fr_0.95fr]">
        <section className="hidden bg-slate-950 text-white lg:flex">
          <div className="flex w-full flex-col justify-between px-14 py-12">
            <div>
              <div className="flex items-center gap-3">
                <div className="grid h-10 w-10 place-items-center rounded bg-cyan-400 font-bold text-slate-950">
                  TB
                </div>
                <div>
                  <p className="text-sm font-semibold uppercase tracking-widest text-cyan-200">
                    Travel Billing System
                  </p>
                  <p className="text-sm text-slate-400">Secure operations console</p>
                </div>
              </div>
              <div className="mt-20 max-w-xl">
                <h1 className="text-5xl font-semibold leading-tight">
                  Billing, vehicles, payments, and travel operations in one secure workspace.
                </h1>
                <p className="mt-6 text-lg leading-8 text-slate-300">
                  Sign in with your assigned role to access the dashboard built for your daily workflow.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4 text-sm text-slate-300">
              <div className="border-t border-white/15 pt-4">
                <p className="font-semibold text-white">Owner</p>
                <p className="mt-1">Full business visibility</p>
              </div>
              <div className="border-t border-white/15 pt-4">
                <p className="font-semibold text-white">Manager</p>
                <p className="mt-1">Operational control</p>
              </div>
              <div className="border-t border-white/15 pt-4">
                <p className="font-semibold text-white">Employee</p>
                <p className="mt-1">Focused daily tasks</p>
              </div>
            </div>
          </div>
        </section>

        <section className="flex items-center justify-center px-5 py-10 sm:px-8">
          <div className="w-full max-w-md">
            <div className="mb-8 lg:hidden">
              <div className="flex items-center gap-3">
                <div className="grid h-10 w-10 place-items-center rounded bg-slate-950 font-bold text-white">
                  TB
                </div>
                <div>
                  <p className="text-sm font-semibold uppercase tracking-widest text-slate-500">
                    Travel Billing System
                  </p>
                  <p className="text-sm text-slate-500">Secure operations console</p>
                </div>
              </div>
            </div>

            <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-panel sm:p-8">
              <div>
                <p className="text-sm font-medium text-cyan-700">Welcome back</p>
                <h2 className="mt-2 text-3xl font-semibold text-slate-950">Sign in</h2>
                <p className="mt-2 text-sm leading-6 text-slate-500">
                  Enter your account credentials to continue.
                </p>
              </div>

              <form className="mt-8 space-y-5" onSubmit={handleSubmit}>
                <div>
                  <label className="text-sm font-medium text-slate-700" htmlFor="username">
                    Username
                  </label>
                  <input
                    className="mt-2 w-full rounded-md border border-slate-300 bg-white px-4 py-3 text-base outline-none transition focus:border-cyan-600 focus:ring-4 focus:ring-cyan-100"
                    id="username"
                    name="username"
                    type="text"
                    autoComplete="username"
                    value={form.username}
                    onChange={handleChange}
                    required
                  />
                </div>

                <div>
                  <label className="text-sm font-medium text-slate-700" htmlFor="password">
                    Password
                  </label>
                  <input
                    className="mt-2 w-full rounded-md border border-slate-300 bg-white px-4 py-3 text-base outline-none transition focus:border-cyan-600 focus:ring-4 focus:ring-cyan-100"
                    id="password"
                    name="password"
                    type="password"
                    autoComplete="current-password"
                    value={form.password}
                    onChange={handleChange}
                    required
                  />
                </div>

                {error ? (
                  <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
                    {error}
                  </div>
                ) : null}

                <button
                  className="flex w-full items-center justify-center rounded-md bg-slate-950 px-4 py-3 text-base font-semibold text-white transition hover:bg-slate-800 focus:outline-none focus:ring-4 focus:ring-slate-300 disabled:cursor-not-allowed disabled:bg-slate-400"
                  type="submit"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? "Signing in..." : "Sign in"}
                </button>
              </form>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
