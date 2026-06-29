import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Plus, MessageSquare, Trash2, Bot, Send, Loader2,
  AlertCircle, Copy, RefreshCw, ChevronDown, ChevronUp,
  Crown, Menu, X, Sparkles,
} from 'lucide-react';
import { useChat } from '../hooks/useChat';
import { formatRelativeTime } from '../utils/formatters';
import Navbar from '../components/layout/Navbar';
import type { ChatMessage } from '../types';

// ===== SUGGESTIONS =====
const SUGGESTIONS = [
  {
    group: '志愿策略',
    items: [
      '什么是冲稳保策略？如何确定我的冲稳保比例？',
      '我的分数刚过一本线，怎么填志愿比较稳妥？',
    ],
  },
  {
    group: '招生与专业',
    items: [
      '什么是专业组？专业组内怎么选专业？调剂是什么意思？',
      '招生章程里有哪些关键信息需要重点看？',
    ],
  },
  {
    group: '数据解读',
    items: [
      '位次和分数哪个更重要？如何用位次定位院校？',
      '大小年是什么意思？如何判断今年是涨还是跌？',
    ],
  },
  {
    group: '择境功能',
    items: [
      '如何保存我的志愿方案？支持导出吗？',
      '进阶版和基础版的推荐结果有什么不同？',
    ],
  },
];

const LOADING_STEPS = [
  { text: '正在分析你的分数和位次…', icon: 'Search' },
  { text: '正在检索官方招生数据…', icon: 'Database' },
  { text: '正在生成个性化建议…', icon: 'BrainCircuit' },
];

// ===== HELPER: Copy to clipboard =====
async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    return false;
  }
}

// ===== LOADING SKELETON COMPONENT =====
function LoadingSkeleton({ step }: { step: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex gap-3"
    >
      <div className="w-8 h-8 rounded-full bg-[#F5F0E8] flex items-center justify-center shrink-0">
        <Bot size={14} className="text-[#1A2E22]" />
      </div>
      <div className="flex-1 space-y-2">
        <div className="flex items-center gap-2 mb-2">
          <div className="w-4 h-4 rounded-full border-2 border-[#1A2E22] border-t-transparent animate-spin" />
          <span className="text-[13px] text-[#7D7464]">
            {LOADING_STEPS[Math.min(step, LOADING_STEPS.length - 1)].text}
          </span>
        </div>
        <div className="space-y-2">
          <div className="h-3 skeleton rounded w-3/4" />
          <div className="h-3 skeleton rounded w-1/2" />
          <div className="h-3 skeleton rounded w-5/6" />
        </div>
      </div>
    </motion.div>
  );
}

export default function Chat() {
  const {
    session,
    sessions,
    messages,
    loading,
    sending,
    error,
    sendMessage,
    createSession,
    switchSession,
    deleteSession,
    fetchSessions,
    retryLastMessage,
    clearChat,
    setSession,
  } = useChat();

  const [input, setInput] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [expandedSources, setExpandedSources] = useState<Record<string, boolean>>({});
  const [loadingStep, setLoadingStep] = useState(0);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Load existing sessions on mount (no auto-create)
  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, sending]);

  // Animate loading steps
  useEffect(() => {
    if (!sending) {
      setLoadingStep(0);
      return;
    }
    const t1 = setTimeout(() => setLoadingStep(1), 1500);
    const t2 = setTimeout(() => setLoadingStep(2), 3500);
    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
    };
  }, [sending]);

  // Auto-resize textarea
  useEffect(() => {
    const ta = textareaRef.current;
    if (ta) {
      ta.style.height = 'auto';
      ta.style.height = Math.min(ta.scrollHeight, 160) + 'px';
    }
  }, [input]);

  const handleSend = useCallback(() => {
    if (!input.trim() || sending) return;
    const content = input.trim();
    setInput('');
    sendMessage(content);
  }, [input, sending, sendMessage]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSuggestionClick = (text: string) => {
    sendMessage(text);
  };

  const handleNewSession = () => {
    setSession(null);
    clearChat();
    setSidebarOpen(false);
  };

  const handleSwitchSession = (id: string) => {
    switchSession(id);
    setSidebarOpen(false);
  };

  const handleDeleteSession = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    deleteSession(id);
  };

  const toggleSources = (msgId: string) => {
    setExpandedSources((prev) => ({ ...prev, [msgId]: !prev[msgId] }));
  };

  const handleCopy = async (msgId: string, text: string) => {
    const success = await copyToClipboard(text);
    if (success) {
      setCopiedId(msgId);
      setTimeout(() => setCopiedId(null), 2000);
    }
  };

  const hasMessages = messages.length > 0;

  // ===== SIDEBAR CONTENT =====
  const sidebarContent = (
    <div className="flex flex-col h-full">
      {/* Top: New Chat Button */}
      <div className="p-3 border-b border-[#E0D8CC]">
        <button
          onClick={handleNewSession}
          className="w-full flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl bg-[#1A2E22] text-white text-sm font-medium hover:bg-[#2D4A3E] transition-colors"
        >
          <Plus size={16} />
          新建对话
        </button>
        <div className="mt-3 px-1">
          <span className="text-[11px] text-[#A09888] uppercase tracking-wider font-medium">
            历史咨询
          </span>
        </div>
      </div>

      {/* Middle: Session List — ONLY scrollable area in sidebar */}
      <div className="flex-1 min-h-0 overflow-y-auto py-1.5 px-2 space-y-0.5">
        {sessions.length === 0 ? (
          <div className="text-center text-[#A09888] text-xs py-8">
            {loading ? '加载中…' : '暂无历史咨询'}
          </div>
        ) : (
          sessions.map((s: any) => {
            const isActive = session?.id === s.id;
            return (
              <div
                key={s.id}
                onClick={() => handleSwitchSession(s.id)}
                className={`group flex items-center gap-2 px-3 py-2.5 rounded-lg cursor-pointer transition-colors text-sm ${
                  isActive
                    ? 'bg-[#E8E0D0] text-[#1A2E22]'
                    : 'text-[#7D7464] hover:bg-[#F0EAE0]'
                }`}
              >
                <MessageSquare
                  size={14}
                  className={`shrink-0 ${isActive ? 'text-[#1A2E22]' : 'text-[#A09888]'}`}
                />
                <span className="flex-1 truncate text-[13px]">{s.title || '新对话'}</span>
                <span className="text-[10px] text-[#A09888] shrink-0">{s.message_count ?? 0}</span>
                <button
                  onClick={(e) => handleDeleteSession(e, s.id)}
                  className="opacity-0 group-hover:opacity-100 transition-opacity p-0.5 rounded hover:bg-red-50 text-[#A09888] hover:text-red-500 shrink-0"
                  title="删除对话"
                >
                  <Trash2 size={12} />
                </button>
              </div>
            );
          })
        )}
      </div>

      {/* Bottom: Dev Mode Badge */}
      <div className="border-t border-[#E0D8CC] p-3">
        <div className="flex items-center gap-2 text-[11px] text-[#A09888]">
          <Crown size={12} className="text-[#C4A45C]" />
          <span>开发模式</span>
          <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
        </div>
      </div>
    </div>
  );

  // ===== EMPTY STATE =====
  const emptyState = (
    <div className="h-full flex flex-col items-center justify-center">
      <div className="w-full text-center">
        {/* Bot icon */}
        <div className="w-12 h-12 rounded-full bg-[#F5F0E8] flex items-center justify-center mx-auto mb-4">
          <Bot size={24} className="text-[#1A2E22]" />
        </div>
        <h1 className="font-serif text-2xl font-medium text-[#1A2E22] mb-2">
          择境 AI 志愿顾问
        </h1>
        <p className="text-sm text-[#8C8278] max-w-md mx-auto mb-8 leading-relaxed">
          我可以结合你的分数、位次、专业偏好和官方资料，解释院校、专业组、调剂风险与志愿方案
        </p>

        {/* Suggestion Cards — same max-w-[760px] as messages and input */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-left">
          {SUGGESTIONS.map((group) => (
            <div key={group.group} className="space-y-2">
              <p className="text-[11px] text-[#A09888] uppercase tracking-wider font-medium">
                {group.group}
              </p>
              {group.items.map((item) => (
                <button
                  key={item}
                  onClick={() => handleSuggestionClick(item)}
                  className="w-full text-left px-4 py-3 rounded-xl bg-white border border-[#E0D8CC] hover:border-[#C4A45C] hover:bg-[#F5F0E8] transition-all text-sm text-[#5C5248] leading-relaxed"
                >
                  {item}
                </button>
              ))}
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  return (
    <div className="h-dvh overflow-hidden flex bg-[#FAFAF9]">
      {/* ===== DESKTOP SIDEBAR ===== */}
      <aside className="hidden md:flex w-[260px] shrink-0 flex-col bg-[#F5F0E8] border-r border-[#E0D8CC] pt-20">
        {sidebarContent}
      </aside>

      {/* ===== RIGHT SIDE ===== */}
      <div className="flex-1 min-w-0 flex flex-col pt-20">
        <Navbar />

        {/* ===== CHAT COLUMN ===== */}
        <div className="flex-1 min-w-0 flex flex-col min-h-0">
          {/* ===== CENTER COLUMN ===== */}
          <div className="max-w-[760px] mx-auto w-full h-full flex flex-col px-4">
            {/* ===== SCROLLABLE MESSAGE AREA ===== */}
          <div className="flex-1 min-h-0 overflow-y-auto [&::-webkit-scrollbar]:hidden" style={{"scrollbarWidth":"none"}}>
            {/* Mobile sidebar toggle — floating button */}
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="md:hidden fixed top-[88px] left-4 z-30 w-9 h-9 rounded-lg flex items-center justify-center bg-white border border-[#E0D8CC] shadow-sm text-[#5C5248] hover:bg-[#F5F0E8] transition-colors"
              aria-label="切换侧边栏"
            >
              {sidebarOpen ? <X size={16} /> : <Menu size={16} />}
            </button>
            {hasMessages ? (
              <div className="py-4 space-y-5">
                {messages.map((msg) => {
                  const isUser = msg.role === 'user';
                  return (
                    <motion.div
                      key={msg.id}
                      initial={{ opacity: 0, y: 6 }}
                      animate={{ opacity: 1, y: 0 }}
                      className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}
                    >
                      {/* Avatar */}
                      <div
                        className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                          isUser
                            ? 'bg-[#1A2E22] text-white'
                            : 'bg-[#F5F0E8] text-[#1A2E22]'
                        }`}
                      >
                        {isUser ? (
                          <span className="text-[11px] font-medium">你</span>
                        ) : (
                          <Bot size={14} />
                        )}
                      </div>

                      {/* Message Bubble */}
                      <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} max-w-[85%] md:max-w-[75%]`}>
                        <div
                          className={`rounded-2xl px-4 py-3 text-[15px] leading-relaxed ${
                            isUser
                              ? 'bg-[#1A2E22] text-white rounded-tr-md'
                              : 'bg-white border border-[#E0D8CC] text-[#4A4A4A] rounded-tl-md'
                          }`}
                        >
                          {msg.content}
                        </div>

                        {/* Action buttons for assistant messages */}
                        {!isUser && (
                          <div className="flex items-center gap-1 mt-1 ml-1">
                            {/* Copy button */}
                            <button
                              onClick={() => handleCopy(msg.id, msg.content)}
                              className="p-1 rounded-md text-[#A09888] hover:text-[#5C5248] hover:bg-[#F5F0E8] transition-colors"
                              title="复制回答"
                            >
                              {copiedId === msg.id ? (
                                <span className="text-[10px] text-green-600 font-medium px-1">已复制</span>
                              ) : (
                                <Copy size={12} />
                              )}
                            </button>

                            {/* Sources toggle */}
                            {msg.sources && msg.sources.length > 0 && (
                              <button
                                onClick={() => toggleSources(msg.id)}
                                className="flex items-center gap-1 p-1 rounded-md text-[#A09888] hover:text-[#5C5248] hover:bg-[#F5F0E8] transition-colors text-[11px]"
                              >
                                <span>{msg.sources.length} 个来源</span>
                                {expandedSources[msg.id] ? (
                                  <ChevronUp size={10} />
                                ) : (
                                  <ChevronDown size={10} />
                                )}
                              </button>
                            )}
                          </div>
                        )}

                        {/* Sources Section */}
                        {!isUser && msg.sources && msg.sources.length > 0 && expandedSources[msg.id] && (
                          <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            className="ml-1 mt-1.5 space-y-1"
                          >
                            {msg.sources.map((src, si) => (
                              <a
                                key={si}
                                href={src.source_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="block text-[11px] text-[#A09888] hover:text-[#1A2E22] bg-[#FAF7F2] rounded-lg px-3 py-1.5 border border-[#E0D8CC] transition-colors"
                              >
                                <span className="font-medium">{src.title}</span>
                                {src.school_name && (
                                  <span className="text-[#B8A898] ml-1">· {src.school_name}</span>
                                )}
                              </a>
                            ))}
                          </motion.div>
                        )}

                        {/* Free tier upgrade hint */}
                        {!isUser && (
                          <div className="ml-1 mt-2">
                            <div className="flex items-center gap-1.5 text-[11px] text-[#A09888]">
                              <Sparkles size={10} />
                              <span>升级进阶版可解锁专业组调剂风险深度分析</span>
                            </div>
                          </div>
                        )}
                      </div>
                    </motion.div>
                  );
                })}

                {/* Loading Skeleton */}
                {sending && <LoadingSkeleton step={loadingStep} />}

                {/* Error State */}
                {error && (
                  <motion.div
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex gap-3"
                  >
                    <div className="w-8 h-8 rounded-full bg-[#F5F0E8] flex items-center justify-center shrink-0">
                      <Bot size={14} className="text-[#1A2E22]" />
                    </div>
                    <div className="bg-red-50 border border-red-200 rounded-2xl rounded-tl-md px-4 py-3 max-w-[70%]">
                      <div className="flex items-center gap-2 text-sm text-red-700">
                        <AlertCircle size={14} />
                        <span>回答生成失败 · 可能是网络或服务暂时不可用</span>
                      </div>
                      <button
                        onClick={retryLastMessage}
                        className="mt-2 flex items-center gap-1 text-xs text-red-600 hover:text-red-800 underline underline-offset-2"
                      >
                        <RefreshCw size={12} />
                        重试
                      </button>
                    </div>
                  </motion.div>
                )}

                <div ref={messagesEndRef} />
              </div>
            ) : loading ? (
              <div className="h-full flex items-center justify-center">
                <Loader2 size={20} className="animate-spin text-[#A09888]" />
              </div>
            ) : (
              emptyState
            )}
          </div>

          {/* ===== COMPOSER ===== */}
          <div className="shrink-0 py-3">
              <div className="flex gap-2 items-start">
                <div className="flex-1 relative">
                  <textarea
                    ref={textareaRef}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="问我关于院校、专业组、招生章程或你的志愿方案的问题…"
                    rows={1}
                    disabled={sending}
                    className="w-full min-h-[52px] max-h-[160px] bg-[#F5F0E8] border border-[#E0D8CC] rounded-2xl px-4 py-3 text-[15px] text-[#1A2E22] placeholder:text-[#B8A898] resize-none outline-none focus:border-[#C4A45C] focus:bg-[#F0EAE0] transition-colors disabled:opacity-50 [&::-webkit-scrollbar]:hidden"
                  />
                </div>
                <button
                  onClick={handleSend}
                  disabled={sending || !input.trim()}
                  className="w-10 h-10 mt-1 rounded-xl bg-[#1A2E22] text-white flex items-center justify-center shrink-0 hover:bg-[#2D4A3E] transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  {sending ? (
                    <Loader2 size={16} className="animate-spin" />
                  ) : (
                    <Send size={16} />
                  )}
                </button>
              </div>
              <p className="text-[10px] text-[#B8A898] text-center pt-2">
                择境 AI 基于 CHSI 官方资料回答
              </p>
          </div>
          {/* END CENTER COLUMN */}
        </div>
        {/* END CHAT COLUMN */}
      </div>
      {/* END RIGHT SIDE */}
    </div>

      {/* ===== MOBILE SIDEBAR DRAWER ===== */}
      <AnimatePresence>
        {sidebarOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="fixed inset-0 bg-black/30 z-30 md:hidden"
              onClick={() => setSidebarOpen(false)}
            />
            {/* Drawer */}
            <motion.aside
              initial={{ x: '-100%' }}
              animate={{ x: 0 }}
              exit={{ x: '-100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 300 }}
              className="fixed inset-y-0 left-0 w-[260px] bg-[#F5F0E8] border-r border-[#E0D8CC] z-40 md:hidden"
            >
              {sidebarContent}
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
