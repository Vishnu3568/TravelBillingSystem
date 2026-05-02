import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import api from "../services/api.js";
import { 
  PlusCircle, History, Building2, Truck, 
  BarChart3, Settings, ShieldCheck, FileText,
  TrendingUp, Users, DollarSign, Calendar,
  CreditCard, LayoutDashboard, LogOut, Bell, Car
} from "lucide-react";

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
  cyan: "bg-cyan-500/10 text-cyan-600 border-cyan-500/20",
  emerald: "bg-emerald-500/10 text-emerald-600 border-emerald-500/20",
  indigo: "bg-indigo-500/10 text-indigo-600 border-indigo-500/20",
  amber: "bg-amber-500/10 text-amber-600 border-amber-500/20",
  slate: "bg-slate-500/10 text-slate-600 border-slate-500/20",
  violet: "bg-violet-500/10 text-violet-600 border-violet-500/20",
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

// AppHeader removed to favor global header in MainLayout


function RevenueChart({ revenueTrend }) {
  const maxValue = Math.max(...revenueTrend.map((item) => item.revenue), 1);

  return (
    <section className="rounded-none border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-black">Revenue Trend</h2>
          <p className="text-sm text-slate-500">Last six months from bills</p>
        </div>
        <p className="text-sm font-semibold text-emerald-700">Live database data</p>
      </div>

      <div className="mt-8 flex h-64 items-end gap-3 sm:gap-5">
        {revenueTrend.map((item) => (
          <div className="flex flex-1 flex-col items-center gap-3" key={item.month}>
            <div className="flex h-52 w-full items-end rounded-none bg-slate-100">
              <div
                className="w-full rounded-none    transition-all duration-300 group-hover: group-hover:"
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
    <section className="rounded-none border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 p-5">
        <h2 className="text-lg font-semibold text-black">Recent Bills</h2>
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
                  <td className="px-5 py-4 font-semibold text-black">{bill.billNumber}</td>
                  <td className="px-5 py-4 text-slate-700">{bill.companyName}</td>
                  <td className="px-5 py-4 text-slate-500">{bill.vehicleRegistrationNumber}</td>
                  <td className="px-5 py-4 font-semibold text-black">{formatMoney(bill.amount)}</td>
                  <td className="px-5 py-4 text-slate-700">{formatMoney(bill.pendingAmount)}</td>
                  <td className="px-5 py-4">
                    <span
                      className={`rounded-none px-2.5 py-1 text-xs font-semibold ${bill.status === "Paid"
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

function QuickActions({ role }) {
  const navigate = useNavigate();

  const actionConfigs = [
    { label: "Create Bill", icon: PlusCircle, path: "/create-bill", desc: "New invoice", color: "bg-black" },
    { label: "History", icon: FileText, path: "/bill-history", desc: "View all bills", color: "bg-black" },
    { label: "Companies", icon: Building2, path: "/companies", desc: "Client master", color: "bg-black" },
    { label: "Vehicles", icon: Car, path: "/vehicles", desc: "Fleet master", color: "bg-black" },
    { label: "Reports", icon: BarChart3, path: "/reports", desc: "Revenue analytics", color: "bg-black" },
    { label: "Users", icon: Users, path: "/users", desc: "Team management", color: "bg-black" },
  ];

  if (role === "OWNER") {
    // Already added in the static list above for simplicity in this replacement
  }

  return (
    <section>
      <h2 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-8 text-center">Quick Actions</h2>
      <div className="grid grid-cols-2 gap-x-4 gap-y-10">
        {actionConfigs.map((action) => (
          <button
            key={action.label}
            onClick={() => navigate(action.path)}
            className="group flex flex-col items-center text-center transition-all hover:-translate-y-1"
          >
            <div className={`mb-4 flex h-16 w-16 items-center justify-center rounded-none text-white transition-all group-hover:scale-110 group-hover:shadow-lg ${action.color}`}>
              <action.icon size={28} />
            </div>
            <h3 className="text-sm font-bold text-black group-hover:text-cyan-600 transition-colors">{action.label}</h3>
            <p className="mt-1 text-[10px] text-slate-500 uppercase tracking-tighter opacity-70">{action.desc}</p>
          </button>
        ))}
      </div>
    </section>
  );
}

function LoadingState() {
  return (
    <div className="mt-6 grid min-h-[320px] place-items-center rounded-none border border-slate-200 bg-white p-8 shadow-sm">
      <div className="text-center">
        <div className="mx-auto h-12 w-12 animate-spin rounded-none border-4 border-slate-200 border-t-cyan-700" />
        <p className="mt-4 text-sm font-semibold text-slate-700">Loading owner dashboard data</p>
        <p className="mt-1 text-sm text-slate-500">Fetching live billing, revenue, and operations metrics.</p>
      </div>
    </div>
  );
}

function SessionExpiredState({ onSignIn }) {
  return (
    <div className="mt-6 rounded-none border border-amber-200 bg-amber-50 p-6 shadow-sm">
      <p className="text-lg font-semibold text-amber-900">Session expired</p>
      <p className="mt-2 max-w-2xl text-sm leading-6 text-amber-800">
        Your login token is missing, expired, or no longer valid. Sign in again to reload the owner dashboard.
      </p>
      <button
        className="mt-5 rounded-none bg-amber-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-amber-800"
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
      { label: "Today Bills", value: formatNumber(stats.todayBillsCount), note: "Today", tone: "cyan", icon: FileText, trend: 12 },
      { label: "Today Revenue", value: formatMoney(stats.todayRevenue), note: "Revenue", tone: "emerald", icon: CreditCard },
      { label: "Monthly Revenue", value: formatMoney(stats.monthlyRevenue), note: "Month", tone: "indigo", icon: DollarSign, trend: 8 },
      { label: "Pending Payments", value: formatMoney(stats.pendingPayments), note: "Overdue", tone: "amber", icon: CreditCard },
      { label: "Total Companies", value: formatNumber(stats.totalCompanies), note: "Clients", tone: "slate", icon: Building2 },
      { label: "Total Vehicles", value: formatNumber(stats.totalVehicles), note: "Fleet", tone: "violet", icon: Truck },
    ];
  }, [dashboard]);

  const revenueTrend = dashboard?.revenueTrend ?? [];
  const recentBills = dashboard?.recentBills ?? [];
  const recentUsersActivity = dashboard?.recentUsersActivity ?? [];

  return (
    <div className="text-black">
      <section className="mx-auto max-w-7xl py-4">
        <div className="relative mb-14 overflow-hidden rounded-none bg-white p-8 text-black shadow-[20px_20px_0px_0px_rgba(0,0,0,1)] border-[3px] border-black mr-[20px]">
          <div className="relative z-10 flex flex-col justify-between gap-6 md:flex-row md:items-center">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <span className="px-2 py-0.5 rounded-none bg-black text-white text-[10px] font-bold uppercase tracking-wider">Workspace</span>
                <span className="w-1.5 h-1.5 rounded-none bg-cyan-500 animate-pulse"></span>
              </div>
              <h2 className="text-3xl font-bold tracking-tight">Welcome back, {username}</h2>
              <p className="mt-3 max-w-xl text-slate-500 text-sm leading-relaxed font-medium">
                Your command center is ready. You have <span className="text-black font-black">{dashboard?.stats?.todayBillsCount || 0} bills</span> pending review for today.
              </p>
            </div>
            
            <div className="flex gap-4">
              <Link 
                to="/create-bill" 
                className="flex items-center gap-2 rounded-none bg-cyan-500 px-6 py-3 text-sm font-bold text-black border-2 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:bg-black hover:text-white transition-all active:translate-x-0.5 active:translate-y-0.5 active:shadow-none"
              >
                <PlusCircle size={18} />
                Create New Bill
              </Link>
            </div>
          </div>
        </div>

        {isSessionExpired ? <SessionExpiredState onSignIn={handleSignInAgain} /> : null}

        {error ? (
          <div className="mb-6 rounded-none border border-red-200 bg-red-50 px-4 py-3 text-sm font-semibold text-red-700">
            {error}
          </div>
        ) : null}

        {/* Metrics removed per request */}

        {isLoading ? (
          <LoadingState />
        ) : isSessionExpired ? null : (
          <>
            <div className="mt-6 grid gap-6 xl:grid-cols-[1fr_360px]">
              <RevenueChart revenueTrend={revenueTrend} />
              <div className="grid gap-6">
                <QuickActions role="OWNER" />
              </div>
            </div>

            <div className="mt-6">
              <RecentBillsTable recentBills={recentBills} />
            </div>
          </>
        )}
      </section>
    </div>
  );
}

function SimpleDashboard({ role, username, logout }) {
  const copy = dashboardCopy[role];

  return (
    <div className="text-black px-6 py-8">
        <div className="rounded-none border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-sm text-slate-500">Signed in as</p>
          <p className="mt-1 text-lg font-semibold">{username}</p>
          <p className="mt-6 text-2xl font-semibold">{copy.subtitle}</p>
        </div>
    </div>
  );
}

export default function DashboardPage({ role }) {
  const { username, logout } = useAuth();

  if (role === "OWNER") {
    return <OwnerDashboard username={username} logout={logout} />;
  }

  return <SimpleDashboard role={role} username={username} logout={logout} />;
}
