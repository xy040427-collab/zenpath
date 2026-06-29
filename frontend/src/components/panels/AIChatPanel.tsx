import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageCircle, Send, Loader2, FileText } from 'lucide-react';
import type { VolunteerItem } from '../../types';

interface AIChatPanelProps {
  item: VolunteerItem;
  profile: Record<string, unknown>;
  dataCoverage: Record<string, unknown>;
}

export default function AIChatPanel({ item, profile, dataCoverage }: AIChatPanelProps) {
  const [expanded, setExpanded] = useState(false);
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [answer, setAnswer] = useState('');
  const [sources, setSources] = useState<Array<{ source_name: string; source_url: string }>>([]);
  const [error, setError] = useState('');

  const handleAsk = async () => {
    if (!question.trim() || loading) return;
    setLoading(true);
    setError('');

    try {
      const resp = await fetch('/api/v1/ai/chat/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: question.trim(),
          profile,
          recommendation: item,
          data_coverage: dataCoverage,
        }),
      });
      const data = await resp.json();
      if (data.success) {
        setAnswer(data.answer || '');
        setSources(data.sources || []);
      } else {
        setError('AI助手暂时无法回答');
      }
    } catch {
      setError('AI助手暂时无法回答');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="border border-cream-200 rounded-xl bg-cream-50 mb-4">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full p-4 flex items-center justify-between text-left hover:bg-cream-100/50 transition-colors rounded-xl"
      >
        <span className="font-serif text-lg text-brand-900 flex items-center gap-2">
          <MessageCircle size={18} /> 追问AI助手
        </span>
        <span className="text-xs text-stone-400">{expanded ? '收起' : '展开'}</span>
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4 space-y-3">
              {/* Input */}
              <div className="flex gap-2">
                <input
                  type="text"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleAsk()}
                  placeholder="例如：这个专业适合我吗？就业怎么样？"
                  className="flex-1 text-sm px-4 py-2 border border-cream-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-brand-900/20"
                  disabled={loading}
                />
                <button
                  onClick={handleAsk}
                  disabled={loading || !question.trim()}
                  className="px-4 py-2 bg-brand-900 text-white rounded-lg text-sm hover:bg-brand-800 transition-colors disabled:opacity-50"
                >
                  {loading ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
                </button>
              </div>

              {/* Answer */}
              {answer && (
                <div className="bg-white rounded-xl p-4 border border-cream-200">
                  <p className="text-sm text-stone-700 leading-relaxed whitespace-pre-line">{answer}</p>
                  {sources.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {sources.map((s, i) => (
                        <span key={i} className="inline-flex items-center gap-1 text-xs bg-cream-50 px-2 py-1 rounded-full text-stone-500">
                          <FileText size={10} /> {s.source_name}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Error */}
              {error && (
                <p className="text-sm text-amber-600 bg-amber-50 rounded-lg p-3">{error}</p>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
