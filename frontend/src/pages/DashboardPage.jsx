import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import api from "../services/api.js";

const dashboardCopy = {
  OWNER: {
    title: "Owner Dashboard",
    subtitle: "Business overview, revenue, billing, and team access.",
  },
  MANAGER: {
    title: "Manager Dashboard",
    subtitle: "Daily operations, vehicles, billing status, and payments.",
  },
  EMPLOYEE: {
    title: "Employee Dashboard",
    subtitle: "Assigned work, customer trips, and billing tasks.",
  },
};

// const quickActions = ["Create Bill", "Bill History", "Manage Companies", "Manage Vehicles", "Reports"];

const toneClasses = {
  cyan: "bg-cyan-50 text-cyan-700 ring-cyan-100",
  emerald: "bg-emerald-50 text-emerald-700 ring-emerald-100",
  indigo: "bg-indigo-50 text-indigo-700 ring-indigo-100",
  amber: "bg-amber-50 text-amber-700 ring-amber-100",
  slate: "bg-slate-100 text-slate-700 ring-slate-200",
  violet: "bg-violet-50 text-violet-700 ring-violet-100",
};

const currencyFormatter = new Intl.NumberFormat("en-IN", {
  maximumFractionDigits: 0,
});

function formatMoney(value) {
  return `INR ${currencyFormatter.format(Number(value || 0))}`;
}

function formatNumber(value) {
  return currencyFormatter.format(Number(value || 0));
}

function formatDateTime(value) {
  if (!value) {
    return "Recently";
  }
  return new Intl.DateTimeFormat("en-IN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function AppHeader({ copy, logout, showOwnerNav = false }) {
  return (
    <header className="border-b border-slate-200 bg-white/95 backdrop-blur">
      <div className="mx-auto flex max-w-7xl flex-col gap-4 px-5 py-4 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-widest text-cyan-700">
            Travel Billing System
          </p>
          <h1 className="text-2xl font-semibold text-slate-950">{copy.title}</h1>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          {showOwnerNav ? (
            <>
              <Link
                className="rounded-md bg-slate-950 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-800"
                to="/create-bill"
              >
                Create Bill
              </Link>
              <Link
                className="rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
                to="/owner-dashboard"
              >
                Dashboard
              </Link>
            </>
          ) : null}
          <button
            className="rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
            type="button"
            onClick={logout}
          >
            Sign out
          </button>
        </div>
      </div>
    </header>
  );
}

function MetricCard({ metric }) {
  return (
    <article className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <p className="text-sm font-medium text-slate-500">{metric.label}</p>
        <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ${toneClasses[metric.tone]}`}>
          {metric.note}
        </span>
      </div>
      <p className="mt-4 text-3xl font-semibold text-slate-950">{metric.value}</p>
    </article>
  );
}

function RevenueChart({ revenueTrend }) {
  const maxValue = Math.max(...revenueTrend.map((item) => item.revenue), 1);

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-950">Revenue Trend</h2>
          <p className="text-sm text-slate-500">Last six months from bills</p>
        </div>
        <p className="text-sm font-semibold text-emerald-700">Live database data</p>
      </div>

      <div className="mt-8 flex h-64 items-end gap-3 sm:gap-5">
        {revenueTrend.map((item) => (
          <div className="flex flex-1 flex-col items-center gap-3" key={item.month}>
            <div className="flex h-52 w-full items-end rounded-md bg-slate-100">
              <div
                className="w-full rounded-md bg-gradient-to-t from-cyan-700 to-cyan-400"
                style={{ height: `${Math.max((item.revenue / maxValue) * 100, item.revenue > 0 ? 8 : 0)}%` }}
                title={formatMoney(item.revenue)}
              />
            </div>
            <span className="text-xs font-semibold text-slate-500">{item.month}</span>
          </div>
        ))}
      </div>
    </section>
  );
}

function RecentBillsTable({ recentBills }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 p-5">
        <h2 className="text-lg font-semibold text-slate-950">Recent Bills</h2>
        <p className="text-sm text-slate-500">Latest billing activity across companies</p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[760px] text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase text-slate-500">
            <tr>
              <th className="px-5 py-3 font-semibold">Bill ID</th>
              <th className="px-5 py-3 font-semibold">Company</th>
              <th className="px-5 py-3 font-semibold">Vehicle</th>
              <th className="px-5 py-3 font-semibold">Amount</th>
              <th className="px-5 py-3 font-semibold">Pending</th>
              <th className="px-5 py-3 font-semibold">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {recentBills.length ? (
              recentBills.map((bill) => (
                <tr className="hover:bg-slate-50" key={bill.id}>
                  <td className="px-5 py-4 font-semibold text-slate-950">{bill.billNumber}</td>
                  <td className="px-5 py-4 text-slate-700">{bill.companyName}</td>
                  <td className="px-5 py-4 text-slate-500">{bill.vehicleRegistrationNumber}</td>
                  <td className="px-5 py-4 font-semibold text-slate-950">{formatMoney(bill.amount)}</td>
                  <td className="px-5 py-4 text-slate-700">{formatMoney(bill.pendingAmount)}</td>
                  <td className="px-5 py-4">
                    <span
                      className={`rounded-full px-2.5 py-1 text-xs font-semibold ${bill.status === "Paid"
                          ? "bg-emerald-50 text-emerald-700"
                          : bill.status === "Pending"
                            ? "bg-amber-50 text-amber-700"
                            : "bg-red-50 text-red-700"
                        }`}
                    >
                      {bill.status}
                    </span>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td className="px-5 py-8 text-center text-slate-500" colSpan="6">
                  No bills found yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function ActivityPanel({ recentUsersActivity }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-950">Recent Users Activity</h2>
      <div className="mt-5 space-y-4">
        {recentUsersActivity.length ? (
          recentUsersActivity.map((activity) => (
            <div className="flex gap-3" key={activity.id}>
              <div className="mt-1 h-2.5 w-2.5 rounded-full bg-cyan-600" />
              <div className="min-w-0 flex-1">
                <p className="font-medium text-slate-950">{activity.action}</p>
                <p className="text-sm text-slate-500">
                  {activity.performedBy} - {formatDateTime(activity.actionTime)}
                </p>
              </div>
            </div>
          ))
        ) : (
          <p className="text-sm text-slate-500">No activity recorded yet.</p>
        )}
      </div>
    </section>
  );
}

function QuickActions({ role }) {
  const navigate = useNavigate();

  const actions = ["Create Bill", "Bill History", "Manage Companies", "Manage Vehicles", "Reports"];
  if (role === "OWNER") {
    actions.push("User Management");
    actions.push("Backup & Restore");
    actions.push("Audit Logs");
    actions.push("Import Word Bills");
  }

  const handleQuickAction = (action) => {
    if (action === "Create Bill") {
      navigate("/create-bill");
    } else if (action === "Bill History") {
      navigate("/bill-history");
    } else if (action === "Manage Companies") {
      navigate("/companies");
    } else if (action === "Manage Vehicles") {
      navigate("/vehicles");
    } else if (action === "Reports") {
      navigate("/reports");
    } else if (action === "User Management") {
      navigate("/users");
    } else if (action === "Backup & Restore") {
      navigate("/backup");
    } else if (action === "Audit Logs") {
      navigate("/audit-logs");
    } else if (action === "Import Word Bills") {
      navigate("/import-word");
    }
  };

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-950">Quick Actions</h2>
      <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
        {actions.map((action) => (
          <button
            className="rounded-md border border-slate-200 bg-slate-50 px-4 py-3 text-left text-sm font-semibold text-slate-800 transition hover:border-cyan-200 hover:bg-cyan-50 hover:text-cyan-800"
            key={action}
            type="button"
            onClick={() => handleQuickAction(action)}
          >
            {action}
          </button>
        ))}
      </div>
    </section>
  );
}

function LoadingState() {
  return (
    <div className="mt-6 grid min-h-[320px] place-items-center rounded-lg border border-slate-200 bg-white p-8 shadow-sm">
      <div className="text-center">
        <div className="mx-auto h-12 w-12 animate-spin rounded-full border-4 border-slate-200 border-t-cyan-700" />
        <p className="mt-4 text-sm font-semibold text-slate-700">Loading owner dashboard data</p>
        <p className="mt-1 text-sm text-slate-500">Fetching live billing, revenue, and operations metrics.</p>
      </div>
    </div>
  );
}

function SessionExpiredState({ onSignIn }) {
  return (
    <div className="mt-6 rounded-lg border border-amber-200 bg-amber-50 p-6 shadow-sm">
      <p className="text-lg font-semibold text-amber-900">Session expired</p>
      <p className="mt-2 max-w-2xl text-sm leading-6 text-amber-800">
        Your login token is missing, expired, or no longer valid. Sign in again to reload the owner dashboard.
      </p>
      <button
        className="mt-5 rounded-md bg-amber-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-amber-800"
        type="button"
        onClick={onSignIn}
      >
        Back to sign in
      </button>
    </div>
  );
}

function OwnerDashboard({ username, logout }) {
  const navigate = useNavigate();
  const [dashboard, setDashboard] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [isSessionExpired, setIsSessionExpired] = useState(false);

  useEffect(() => {
    let ignore = false;

    async function loadDashboard() {
      try {
        setIsLoading(true);
        const response = await api.get("/dashboard/owner");
        if (!ignore) {
          setDashboard(response.data);
          setError("");
        }
      } catch (requestError) {
        if (!ignore) {
          const status = requestError.response?.status;
          if (status === 401 || status === 403) {
            setIsSessionExpired(true);
            setError("");
            return;
          }
          setError("Could not load dashboard data. Please check that the backend is running.");
        }
      } finally {
        if (!ignore) {
          setIsLoading(false);
        }
      }
    }

    loadDashboard();
    return () => {
      ignore = true;
    };
  }, []);

  const handleSignInAgain = () => {
    logout();
    navigate("/login", { replace: true });
  };

  const metrics = useMemo(() => {
    const stats = dashboard?.stats ?? {};
    return [
      { label: "Today Bills Count", value: formatNumber(stats.todayBillsCount), note: "Today", tone: "cyan" },
      { label: "Today Revenue", value: formatMoney(stats.todayRevenue), note: "Bills", tone: "emerald" },
      { label: "Monthly Revenue", value: formatMoney(stats.monthlyRevenue), note: "This month", tone: "indigo" },
      { label: "Pending Payments", value: formatMoney(stats.pendingPayments), note: "Outstanding", tone: "amber" },
      { label: "Total Companies", value: formatNumber(stats.totalCompanies), note: "Active records", tone: "slate" },
      { label: "Total Vehicles", value: formatNumber(stats.totalVehicles), note: "Fleet", tone: "violet" },
    ];
  }, [dashboard]);

  const revenueTrend = dashboard?.revenueTrend ?? [];
  const recentBills = dashboard?.recentBills ?? [];
  const recentUsersActivity = dashboard?.recentUsersActivity ?? [];

  return (
    <main className="min-h-screen bg-slate-100 text-slate-950">
      <AppHeader copy={dashboardCopy.OWNER} logout={logout} showOwnerNav />

      <section className="mx-auto max-w-7xl px-5 py-8">
        <div className="mb-8 flex flex-col justify-between gap-4 rounded-lg bg-slate-950 p-6 text-white shadow-panel md:flex-row md:items-end">
          <div>
            <p className="text-sm font-semibold uppercase tracking-widest text-cyan-200">Executive workspace</p>
            <h2 className="mt-3 text-3xl font-semibold">Good to see you, {username}</h2>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-300">
              Monitor revenue, billing velocity, pending collections, and operational capacity from one command center.
            </p>
          </div>
          <div className="rounded-md bg-white/10 px-4 py-3">
            <p className="text-xs uppercase tracking-widest text-slate-300">Data source</p>
            <p className="mt-1 text-lg font-semibold">Live database</p>
          </div>
        </div>

        {isSessionExpired ? <SessionExpiredState onSignIn={handleSignInAgain} /> : null}

        {error ? (
          <div className="mb-6 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm font-semibold text-red-700">
            {error}
          </div>
        ) : null}

        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {metrics.map((metric) => (
            <MetricCard key={metric.label} metric={metric} />
          ))}
        </div>

        {isLoading ? (
          <LoadingState />
        ) : isSessionExpired ? null : (
          <>
            <div className="mt-6 grid gap-6 xl:grid-cols-[1fr_360px]">
              <RevenueChart revenueTrend={revenueTrend} />
              <div className="grid gap-6">
                <QuickActions role="OWNER" />
                <ActivityPanel recentUsersActivity={recentUsersActivity} />
              </div>
            </div>

            <div className="mt-6">
              <RecentBillsTable recentBills={recentBills} />
            </div>
          </>
        )}
      </section>
    </main>
  );
}

function SimpleDashboard({ role, username, logout }) {
  const copy = dashboardCopy[role];

  return (
    <main className="min-h-screen bg-slate-100 text-slate-950">
      <AppHeader copy={copy} logout={logout} />

      <section className="mx-auto max-w-6xl px-5 py-10">
        <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-sm text-slate-500">Signed in as</p>
          <p className="mt-1 text-lg font-semibold">{username}</p>
          <p className="mt-6 text-2xl font-semibold">{copy.subtitle}</p>
        </div>
      </section>
    </main>
  );
}

export default function DashboardPage({ role }) {
  const { username, logout } = useAuth();

  if (role === "OWNER") {
    return <OwnerDashboard username={username} logout={logout} />;
  }

  return <SimpleDashboard role={role} username={username} logout={logout} />;
}
