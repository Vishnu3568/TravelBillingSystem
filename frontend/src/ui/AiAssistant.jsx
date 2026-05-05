import React, { useState, useRef, useEffect } from 'react';
import { MessageSquare, Send, X, Bot, User, Sparkles, Loader2, Minimize2 } from 'lucide-react';
import api from '../services/api';

export default function AiAssistant({ billId = null }) {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hello! I am your Billing Assistant. Ask me anything about your bills or revenue stats.', time: new Date() }
  ]);
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!query.trim() || loading) return;

    const userMessage = { role: 'user', content: query, time: new Date() };
    setMessages(prev => [...prev, userMessage]);
    setQuery('');
    setLoading(true);

    try {
      const response = await api.post(`/analytics/assistant?query=${encodeURIComponent(query)}${billId ? `&billId=${billId}` : ''}`);
      const aiMessage = { 
        role: 'assistant', 
        content: response.data.answer, 
        confidence: response.data.confidence,
        references: response.data.references,
        time: new Date() 
      };
      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      const errorMsg = error.response?.data?.answer || error.response?.data?.message || 'Sorry, I encountered an error connecting to the intelligence server.';
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

  if (!isOpen) {
    return (
      <button 
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 w-14 h-14 bg-black text-cyan-500 rounded-none border-2 border-cyan-500 shadow-[4px_4px_0px_0px_rgba(6,182,212,0.5)] flex items-center justify-center hover:scale-110 transition-all z-50 animate-bounce"
      >
        <MessageSquare size={24} />
      </button>
    );
  }

  return (
    <div className="fixed bottom-6 right-6 w-[350px] sm:w-[400px] h-[500px] bg-black border-2 border-cyan-500 shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] flex flex-col z-50 overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-cyan-500/30 flex items-center justify-between bg-slate-900">
        <div className="flex items-center gap-2">
          <Sparkles size={18} className="text-cyan-500 animate-pulse" />
          <h3 className="font-black text-xs uppercase tracking-widest text-white">Billing Assistant</h3>
          {billId && <span className="text-[10px] bg-cyan-500/10 text-cyan-500 px-1.5 py-0.5 border border-cyan-500/20">Bill Context</span>}
        </div>
        <button onClick={() => setIsOpen(false)} className="text-slate-400 hover:text-white transition-colors">
          <Minimize2 size={18} />
        </button>
      </div>

      {/* Messages */}
      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')]"
      >
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[85%] p-3 rounded-none border ${
              msg.role === 'user' 
                ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-100' 
                : msg.error ? 'bg-red-500/10 border-red-500/30 text-red-200' : 'bg-slate-800 border-slate-700 text-slate-200'
            }`}>
              <div className="flex items-center gap-2 mb-1 opacity-50">
                {msg.role === 'user' ? <User size={10} /> : <Bot size={10} />}
                <span className="text-[8px] font-bold uppercase tracking-tighter">
                  {msg.role === 'user' ? 'You' : 'Assistant'} • {msg.time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
              <p className="text-xs leading-relaxed font-medium whitespace-pre-wrap">{msg.content}</p>
              {msg.references && msg.references.length > 0 && (
                <div className="mt-2 pt-2 border-t border-slate-700 text-[10px] text-slate-500 italic">
                  Ref: {msg.references.join(', ')}
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-slate-800 border border-slate-700 p-3 flex items-center gap-2">
              <Loader2 size={14} className="text-cyan-500 animate-spin" />
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-tighter">AI is thinking...</span>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <form onSubmit={handleSend} className="p-3 border-t border-cyan-500/30 bg-slate-900">
        <div className="flex gap-2">
          <input 
            type="text" 
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask a question..."
            className="flex-1 bg-black border border-slate-700 px-3 py-2 text-xs text-white focus:border-cyan-500 outline-none transition-all placeholder:text-slate-600"
          />
          <button 
            disabled={loading || !query.trim()}
            className="bg-cyan-500 text-black px-3 py-2 hover:bg-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send size={16} />
          </button>
        </div>
      </form>
    </div>
  );
}
