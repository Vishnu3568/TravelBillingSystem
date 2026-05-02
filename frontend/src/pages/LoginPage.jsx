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
    <main className="min-h-screen bg-slate-50 text-black">
      <div className="grid min-h-screen lg:grid-cols-[1.05fr_0.95fr]">
        {/* Left Side (Desktop Only) */}
        <section className="hidden bg-black text-white lg:flex">
          <div className="flex w-full flex-col justify-between px-14 py-12">
            <div>
              <div className="flex items-center gap-3">
                <div className="grid h-10 w-10 place-items-center rounded-none bg-cyan-400 font-bold text-black">
                  STB
                </div>
                <div>
                  <p className="text-sm font-semibold uppercase tracking-widest text-white">
                    Sri Tulja Bhavani Travels
                  </p>
                  <p className="text-sm text-slate-400">Rent a car Billing System</p>
                </div>
              </div>
              <div className="mt-20 max-w-xl">
                <h1 className="text-5xl font-semibold leading-tight">
                  Billing, vehicles, payments, and travel operations in one secure workspace.
                </h1>
                <p className="mt-6 text-lg leading-8 text-cyan-400 font-medium">
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

        {/* Right Side / Mobile Flow */}
        <section className="flex flex-col items-center justify-center p-0 lg:px-8">
          <div className="w-full">
            {/* Mobile Header (Top) */}
            <div className="lg:hidden bg-white px-6 py-8 border-b border-slate-200">
              <div className="flex items-center gap-3">
                <div className="grid h-10 w-10 place-items-center rounded-none bg-cyan-500 font-black text-black">
                  STB
                </div>
                <div>
                  <p className="text-sm font-bold uppercase tracking-widest text-black leading-none">
                    Sri Tulja Bhavani Travels
                  </p>
                  <p className="text-[10px] text-slate-500 uppercase tracking-widest mt-1">Rent a car Billing System</p>
                </div>
              </div>
            </div>

            <div className="max-w-md mx-auto w-full px-6 py-12">
              <div className="rounded-none border-2 border-black bg-white p-6 shadow-[10px_10px_0px_0px_rgba(0,0,0,1)] sm:p-8">
                <div>
                  <p className="text-sm font-bold text-cyan-600 uppercase tracking-widest">Welcome back</p>
                  <h2 className="mt-2 text-3xl font-black text-black uppercase tracking-tight">Sign in</h2>
                </div>

                <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
                  <div>
                    <label className="text-xs font-bold text-slate-400 uppercase tracking-widest" htmlFor="username">
                      Username
                    </label>
                    <input
                      className="mt-2 w-full rounded-none border-2 border-slate-200 bg-white px-4 py-3 text-base outline-none transition focus:border-black focus:ring-0"
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
                    <label className="text-xs font-bold text-slate-400 uppercase tracking-widest" htmlFor="password">
                      Password
                    </label>
                    <input
                      className="mt-2 w-full rounded-none border-2 border-slate-200 bg-white px-4 py-3 text-base outline-none transition focus:border-black focus:ring-0"
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
                    <div className="rounded-none border-2 border-red-200 bg-red-50 px-4 py-3 text-sm font-bold text-red-700">
                      {error}
                    </div>
                  ) : null}

                  <button
                    className="flex w-full items-center justify-center rounded-none bg-cyan-500 px-4 py-4 text-sm font-bold text-black border-2 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:bg-black hover:text-white transition-all active:translate-x-0.5 active:translate-y-0.5 active:shadow-none disabled:cursor-not-allowed disabled:bg-slate-300 uppercase tracking-widest"
                    type="submit"
                    disabled={isSubmitting}
                  >
                    {isSubmitting ? "Signing in..." : "Sign in"}
                  </button>
                </form>
              </div>
            </div>

            {/* Mobile Hero & Roles (Bottom) */}
            <div className="lg:hidden bg-black text-white px-6 py-12">
              <div className="max-w-md mx-auto">
                <h2 className="text-3xl font-bold leading-tight">
                  Billing, vehicles, payments, and travel operations in one secure workspace.
                </h2>
                <p className="mt-4 text-sm leading-relaxed text-cyan-400 font-medium">
                  Sign in with your assigned role to access the dashboard built for your daily workflow.
                </p>

                <div className="mt-12 space-y-6">
                  <div className="border-l-2 border-cyan-500 pl-4">
                    <p className="font-bold text-white uppercase tracking-widest text-xs">Owner</p>
                    <p className="mt-1 text-slate-400 text-sm">Full business visibility</p>
                  </div>
                  <div className="border-l-2 border-cyan-500 pl-4">
                    <p className="font-bold text-white uppercase tracking-widest text-xs">Manager</p>
                    <p className="mt-1 text-slate-400 text-sm">Operational control</p>
                  </div>
                  <div className="border-l-2 border-cyan-500 pl-4">
                    <p className="font-bold text-white uppercase tracking-widest text-xs">Employee</p>
                    <p className="mt-1 text-slate-400 text-sm">Focused daily tasks</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
