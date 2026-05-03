import React, { useState, useEffect } from 'react';
import { TrendingUp, Bell, FileText, Sparkles } from 'lucide-react';
import api from '../services/api';

export default function AiInsightsSidebar() {
  const [insights, setInsights] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchInsights() {
      try {
        const response = await api.get("/analytics/ai-insights");
        setInsights(response.data.insights || []);
      } catch (error) {
        console.error("Failed to fetch AI insights:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchInsights();
  }, []);

  if (loading) return (
    <div className="mt-8 pt-8 border-t border-slate-800 animate-pulse">
      <div className="h-4 w-24 bg-slate-800 mb-4"></div>
      <div className="space-y-3">
        <div className="h-10 bg-slate-800/50 w-full"></div>
        <div className="h-10 bg-slate-800/50 w-full"></div>
      </div>
    </div>
  );

  if (insights.length === 0) return null;

  return (
    <div className="mt-8 pt-8 border-t border-slate-800">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-[10px] font-black uppercase tracking-[0.2em] text-cyan-500">AI Intelligence</h3>
        <Sparkles size={12} className="text-cyan-500 animate-pulse" />
      </div>

      <div className="space-y-3 max-h-[300px] overflow-y-auto pr-2 custom-scrollbar">
        {insights.map((insight, i) => (
          <div key={i} className="group p-3 bg-slate-900 border-l-2 transition-all hover:bg-slate-800"
               style={{ borderColor: insight.type === 'WARNING' ? '#f59e0b' : insight.type === 'TREND' ? '#10b981' : '#06b6d4' }}>
            <p className="text-[11px] font-bold text-slate-200 leading-snug group-hover:text-white transition-colors">
              {insight.message}
            </p>
            <div className="mt-2 flex items-center justify-between">
              <span className={`text-[8px] font-black uppercase tracking-tighter 
                ${insight.type === 'WARNING' ? 'text-amber-500' : insight.type === 'TREND' ? 'text-emerald-500' : 'text-cyan-500'}`}>
                {insight.type}
              </span>
              <div className="w-10 h-0.5 bg-slate-800">
                <div className="h-full bg-slate-400" style={{ width: `${insight.confidence * 100}%` }}></div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
