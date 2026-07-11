import React, { useState, useRef, useEffect } from 'react';
import { MessageSquare, Send, X, Bot, User, Sparkles, Loader2, RotateCcw, HelpCircle, BarChart2, Shield, Search } from 'lucide-react';
import api from '../services/api';
import { toast } from 'sonner';

export default function AiAssistant({ billId = null }) {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [sessionId] = useState(() => 'session_' + Math.random().toString(36).substr(2, 9));
  const [messages, setMessages] = useState([
    { 
      role: 'assistant', 
      content: 'Hello! I am your Enterprise AI Copilot. I have real-time access to layout patterns, validation reports, and historical reviewer corrections. Ask me anything!', 
      time: new Date() 
    }
  ]);
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef(null);

  // Auto scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isOpen]);

  const handleSend = async (e, customQuery = null) => {
    if (e) e.preventDefault();
    const activeQuery = customQuery || query;
    if (!activeQuery.trim() || loading) return;

    const userMessage = { role: 'user', content: activeQuery, time: new Date() };
    setMessages(prev => [...prev, userMessage]);
    if (!customQuery) setQuery('');
    setLoading(true);

    try {
      const response = await api.post('/copilot/chat', {
        query: activeQuery,
        sessionId: sessionId,
        billId: billId ? parseInt(billId) : null
      });
      
      const aiData = response.data;
      const aiMessage = { 
        role: 'assistant', 
        content: aiData.answer, 
        confidence: aiData.confidence,
        references: aiData.references,
        action: aiData.action,
        time: new Date() 
      };
      setMessages(prev => [...prev, aiMessage]);

      if (aiData.action) {
        toast.info(`Copilot action triggered: ${aiData.action.type}`);
      }
    } catch (error) {
      const errorMsg = error.response?.data?.message || 'Sorry, I encountered an error connecting to the Copilot service.';
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: errorMsg, 
        error: true,
        time: new Date() 
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleClearMemory = async () => {
    try {
      await api.delete(`/copilot/memory/${sessionId}`);
      setMessages([
        { 
          role: 'assistant', 
          content: 'Conversation memory cleared. Ready for your next questions!', 
          time: new Date() 
        }
      ]);
      toast.success('Copilot memory cleared.');
    } catch (error) {
      toast.error('Failed to clear Copilot memory.');
    }
  };

  // Suggested Questions based on context
  const getSuggestedQuestions = () => {
    const questions = [
      "What are our top revenue companies?",
      "Which fields are corrected most?",
      "Show confidence trends."
    ];
    if (billId) {
      questions.unshift("Why was this bill flagged?");
    }
    return questions;
  };

  if (!isOpen) {
    return (
      <button 
        onClick={() => setIsOpen(true)}
        className="fixed right-0 top-1/3 z-50 bg-black text-cyan-500 border-l-2 border-y-2 border-cyan-500 px-3 py-4 flex flex-col items-center gap-2 hover:bg-slate-900 transition-all font-bold text-[10px] tracking-widest uppercase cursor-pointer"
        style={{ writingMode: 'vertical-lr' }}
      >
        <Sparkles className="mb-2 text-cyan-500 animate-pulse" size={14} />
        AI COPILOT
      </button>
    );
  }

  return (
    <div className="fixed right-0 top-0 h-full w-[400px] bg-slate-900 border-l border-cyan-500/40 flex flex-col z-50 shadow-2xl transition-all">
      {/* Header */}
      <div className="p-4 border-b border-cyan-500/30 flex items-center justify-between bg-black">
        <div className="flex items-center gap-2">
          <Sparkles size={18} className="text-cyan-500 animate-pulse" />
          <div>
            <h3 className="font-black text-xs uppercase tracking-widest text-white">Enterprise AI Copilot</h3>
            <p className="text-[8px] text-slate-400">Context-aware ERP Assistant</p>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          <button 
            onClick={handleClearMemory}
            title="Clear Conversation History"
            className="text-slate-400 hover:text-white transition-colors cursor-pointer"
          >
            <RotateCcw size={16} />
          </button>
          <button 
            onClick={() => setIsOpen(false)} 
            className="text-slate-400 hover:text-white transition-colors cursor-pointer"
          >
            <X size={18} />
          </button>
        </div>
      </div>

      {/* Message Area */}
      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-950/60"
      >
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[90%] p-3 border ${
              msg.role === 'user' 
                ? 'bg-cyan-950/40 border-cyan-500/30 text-cyan-100' 
                : msg.error 
                  ? 'bg-rose-950/40 border-rose-500/30 text-rose-200' 
                  : 'bg-slate-900 border-slate-800 text-slate-200'
            }`}>
              <div className="flex items-center justify-between gap-4 mb-1 opacity-50 text-[8px] font-bold uppercase tracking-tighter">
                <span className="flex items-center gap-1">
                  {msg.role === 'user' ? <User size={8} /> : <Bot size={8} />}
                  {msg.role === 'user' ? 'You' : 'Assistant'}
                </span>
                <span>{msg.time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
              </div>
              
              <div className="text-xs leading-relaxed font-medium whitespace-pre-wrap">{msg.content}</div>

              {msg.confidence !== undefined && (
                <div className="mt-2 text-[9px] font-semibold text-cyan-500 flex items-center gap-1">
                  <Shield size={10} /> Confidence: {Math.round(msg.confidence * 100)}%
                </div>
              )}

              {msg.references && msg.references.length > 0 && (
                <div className="mt-2 pt-1.5 border-t border-slate-800 text-[9px] text-slate-500 font-mono">
                  References: {msg.references.join(', ')}
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-slate-900 border border-slate-800 p-3 flex items-center gap-2">
              <Loader2 size={12} className="text-cyan-500 animate-spin" />
              <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest">Generating Context...</span>
            </div>
          </div>
        )}
      </div>

      {/* Suggested Questions & Input */}
      <div className="p-4 border-t border-cyan-500/30 bg-black space-y-4">
        {/* Suggestions */}
        <div className="space-y-1.5">
          <span className="text-[8px] font-black text-slate-500 uppercase tracking-widest block">Suggested Queries</span>
          <div className="flex flex-wrap gap-1.5">
            {getSuggestedQuestions().map((qText, idx) => (
              <button
                key={idx}
                onClick={(e) => handleSend(e, qText)}
                disabled={loading}
                className="text-[9px] px-2.5 py-1.5 bg-slate-900 hover:bg-slate-800 text-cyan-400 border border-cyan-500/25 hover:border-cyan-500/50 transition-all font-semibold cursor-pointer disabled:opacity-50"
              >
                {qText}
              </button>
            ))}
          </div>
        </div>

        {/* Input bar */}
        <form onSubmit={handleSend} className="flex gap-2">
          <input 
            type="text" 
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask AI Copilot..."
            className="flex-1 bg-slate-900 border border-slate-800 px-3 py-2.5 text-xs text-white focus:border-cyan-500 outline-none transition-all placeholder:text-slate-600 font-medium"
          />
          <button 
            disabled={loading || !query.trim()}
            className="bg-cyan-500 text-black px-4 py-2 hover:bg-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-bold text-xs uppercase cursor-pointer"
          >
            Ask
          </button>
        </form>
      </div>
    </div>
  );
}
