import React, { useEffect, useState } from "react";
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  Cell
} from "recharts";
import { 
  TrendingUp, 
  Users, 
  Car, 
  FileText, 
  DollarSign,
  BarChart3,
  Calendar,
  Loader2
} from "lucide-react";
import api from "../services/api";

const COLORS = ["#0ea5e9", "#10b981", "#6366f1", "#f59e0b", "#ef4444"];

const ReportsPage = () => {
  const [summary, setSummary] = useState(null);
  const [topCompanies, setTopCompanies] = useState([]);
  const [topVehicles, setTopVehicles] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchReports = async () => {
      try {
        setLoading(true);
        const [summaryRes, companiesRes, vehiclesRes] = await Promise.all([
          api.get("/reports/summary"),
          api.get("/reports/top-companies"),
          api.get("/reports/top-vehicles")
        ]);
        setSummary(summaryRes.data);
        setTopCompanies(companiesRes.data);
        setTopVehicles(vehiclesRes.data);
      } catch (err) {
        console.error("Error fetching reports:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchReports();
  }, []);

  const formatCurrency = (value) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0
    }).format(value);
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-slate-50">
        <Loader2 className="animate-spin text-indigo-600 mb-4" size={48} />
        <p className="text-slate-600 font-medium text-lg">Generating analytical reports...</p>
      </div>
    );
  }

  const cards = [
    { label: "Today Bills", value: summary?.todayBillsCount, icon: FileText, color: "bg-blue-50 text-blue-600" },
    { label: "Today Revenue", value: formatCurrency(summary?.todayRevenue), icon: DollarSign, color: "bg-emerald-50 text-emerald-600" },
    { label: "Monthly Bills", value: summary?.monthlyBillsCount, icon: Calendar, color: "bg-indigo-50 text-indigo-600" },
    { label: "Monthly Revenue", value: formatCurrency(summary?.monthlyRevenue), icon: TrendingUp, color: "bg-violet-50 text-violet-600" },
    { label: "Total Bills", value: summary?.totalBills, icon: FileText, color: "bg-slate-100 text-slate-600" },
    { label: "Total Companies", value: summary?.totalCompanies, icon: Users, color: "bg-amber-50 text-amber-600" },
    { label: "Total Vehicles", value: summary?.totalVehicles, icon: Car, color: "bg-slate-100 text-slate-600" },
  ];

  return (
    <div className="p-6 bg-slate-50 min-h-screen">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-black flex items-center gap-3">
            <BarChart3 className="text-indigo-600" size={32} />
            Reports & Analytics
          </h1>
          <p className="text-slate-500 mt-2">In-depth analysis of your travel billing operations</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-10">
          {cards.map((card, i) => (
            <div key={i} className="bg-white p-6 rounded-none shadow-sm border border-slate-200 flex items-center gap-5 transition-all hover:shadow-md hover:-translate-y-1">
              <div className={`p-4 rounded-none ${card.color}`}>
                <card.icon size={28} />
              </div>
              <div>
                <p className="text-sm font-medium text-slate-500 mb-1 uppercase tracking-wider">{card.label}</p>
                <p className="text-2xl font-bold text-black">{card.value}</p>
              </div>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-10">
          <div className="bg-white p-6 rounded-none shadow-sm border border-slate-200">
            <h2 className="text-xl font-bold text-slate-800 mb-6 flex items-center gap-2">
              <Users className="text-indigo-600" size={24} />
              Top 5 Companies by Revenue
            </h2>
            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={topCompanies} layout="vertical" margin={{ left: 20, right: 30, top: 20, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="#f1f5f9" />
                  <XAxis type="number" hide />
                  <YAxis 
                    dataKey="name" 
                    type="category" 
                    width={150} 
                    axisLine={false} 
                    tickLine={false}
                    tick={{ fill: '#64748b', fontSize: 12, fontWeight: 500 }}
                  />
                  <Tooltip 
                    cursor={{ fill: '#f8fafc' }}
                    contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)' }}
                    formatter={(value) => formatCurrency(value)}
                  />
                  <Bar dataKey="revenue" radius={[0, 8, 8, 0]} barSize={32}>
                    {topCompanies.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="bg-white p-6 rounded-none shadow-sm border border-slate-200">
            <h2 className="text-xl font-bold text-slate-800 mb-6 flex items-center gap-2">
              <Car className="text-indigo-600" size={24} />
              Top 5 Vehicles by Revenue
            </h2>
            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={topVehicles} layout="vertical" margin={{ left: 20, right: 30, top: 20, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="#f1f5f9" />
                  <XAxis type="number" hide />
                  <YAxis 
                    dataKey="name" 
                    type="category" 
                    width={150} 
                    axisLine={false} 
                    tickLine={false}
                    tick={{ fill: '#64748b', fontSize: 12, fontWeight: 500 }}
                  />
                  <Tooltip 
                    cursor={{ fill: '#f8fafc' }}
                    contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)' }}
                    formatter={(value) => formatCurrency(value)}
                  />
                  <Bar dataKey="revenue" radius={[0, 8, 8, 0]} barSize={32}>
                    {topVehicles.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="bg-white rounded-none shadow-sm border border-slate-200 overflow-hidden">
            <div className="p-5 border-b border-slate-100 bg-slate-50/50">
              <h3 className="font-bold text-slate-800">Top Companies Detailed</h3>
            </div>
            <table className="w-full text-left">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Company</th>
                  <th className="px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider text-right">Revenue</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {topCompanies.map((c, i) => (
                  <tr key={i} className="hover:bg-slate-50 transition-colors">
                    <td className="px-6 py-4 font-medium text-slate-700">{c.name}</td>
                    <td className="px-6 py-4 text-right font-bold text-black">{formatCurrency(c.revenue)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="bg-white rounded-none shadow-sm border border-slate-200 overflow-hidden">
            <div className="p-5 border-b border-slate-100 bg-slate-50/50">
              <h3 className="font-bold text-slate-800">Top Vehicles Detailed</h3>
            </div>
            <table className="w-full text-left">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Vehicle</th>
                  <th className="px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider text-right">Revenue</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {topVehicles.map((v, i) => (
                  <tr key={i} className="hover:bg-slate-50 transition-colors">
                    <td className="px-6 py-4 font-medium text-slate-700">{v.name}</td>
                    <td className="px-6 py-4 text-right font-bold text-black">{formatCurrency(v.revenue)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReportsPage;
