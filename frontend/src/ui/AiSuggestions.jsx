import React, { useState, useEffect } from 'react';
import { Sparkles, Check, ArrowRight, Loader2, Info } from 'lucide-react';
import api from '../services/api';

export default function AiSuggestions({ currentBill, onApply }) {
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchSuggestions = async () => {
      if (!currentBill.companyName || !currentBill.vehicleType) {
        setSuggestions([]);
        return;
      }

      setLoading(true);
      try {
        const response = await api.post('/analytics/suggestions', {
          companyName: currentBill.companyName,
          vehicleType: currentBill.vehicleType,
          totalKm: currentBill.totalKms || 0,
          totalHours: currentBill.totalHours || 0
        });
        setSuggestions(response.data.suggestions || []);
      } catch (error) {
        console.error('Failed to fetch AI suggestions:', error);
      } finally {
        setLoading(false);
      }
    };

    const timer = setTimeout(fetchSuggestions, 1000); // Debounce
    return () => clearTimeout(timer);
  }, [currentBill.companyName, currentBill.vehicleType]);

  if (loading) {
    return (
      <div className="p-4 border-2 border-dashed border-cyan-500/30 bg-cyan-500/5 animate-pulse flex items-center justify-center gap-3">
        <Loader2 size={16} className="text-cyan-500 animate-spin" />
        <span className="text-[10px] font-bold uppercase tracking-widest text-cyan-500/70">AI Analyzing History...</span>
      </div>
    );
  }

  if (suggestions.length === 0) return null;

  return (
    <div className="bg-slate-900 border-2 border-cyan-500/30 overflow-hidden">
      <div className="bg-cyan-500/10 p-2 border-b border-cyan-500/20 flex items-center gap-2">
        <Sparkles size={14} className="text-cyan-500" />
        <h4 className="text-[10px] font-black uppercase tracking-tighter text-white">AI Billing Suggestions</h4>
      </div>
      <div className="divide-y divide-cyan-500/10">
        {suggestions.map((s, i) => (
          <div key={i} className="p-3 hover:bg-white/5 transition-colors group">
            <div className="flex justify-between items-start mb-1">
              <span className="text-[9px] font-bold text-slate-500 uppercase tracking-widest">{s.field}</span>
              <div className={`text-[8px] px-1.5 py-0.5 font-bold ${s.confidence > 0.8 ? 'bg-green-500/20 text-green-400' : 'bg-amber-500/20 text-amber-400'}`}>
                {Math.round(s.confidence * 100)}% Match
              </div>
            </div>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs font-bold text-white">₹{s.suggestedValue}</span>
              <p className="text-[10px] text-slate-400 italic">"{s.reason}"</p>
            </div>
            <button 
              onClick={() => onApply(s.field, s.suggestedValue)}
              className="w-full py-1.5 bg-cyan-500 text-black text-[9px] font-black uppercase tracking-widest flex items-center justify-center gap-2 hover:bg-white transition-all opacity-0 group-hover:opacity-100"
            >
              Apply Suggestion <ArrowRight size={12} />
            </button>
          </div>
        ))}
      </div>
      <div className="p-2 bg-black/40 flex items-start gap-2">
        <Info size={10} className="text-slate-500 mt-0.5" />
        <p className="text-[8px] text-slate-500 leading-tight">These suggestions are based on historical patterns for {currentBill.companyName}. Review carefully before applying.</p>
      </div>
    </div>
  );
}
