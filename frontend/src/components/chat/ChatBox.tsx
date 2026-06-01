'use client';

import React, { useRef, useEffect } from 'react';
import { useChat, LoadingStep } from '../../store/chatContext';
import { ChatMessage } from './ChatMessage';
import { useChatStream } from '../../hooks/useChatStream';
import {
  Sparkles, MessageSquare, Terminal, Lightbulb, GraduationCap,
  ShieldCheck, Brain, Search, BarChart3, Wand2, CheckCircle2
} from 'lucide-react';

// Step definitions for the progress indicator
const STEPS: Array<{
  key: LoadingStep;
  label: string;
  sublabel: string;
  Icon: React.FC<{ className?: string }>;
  color: string;
  ringColor: string;
}> = [
  {
    key: 'validating',
    label: 'Kiểm tra bảo mật',
    sublabel: 'Xác thực đầu vào & phân quyền',
    Icon: ShieldCheck,
    color: 'text-emerald-400',
    ringColor: 'ring-emerald-500/40 bg-emerald-500/10',
  },
  {
    key: 'thinking',
    label: 'Phân tích yêu cầu',
    sublabel: 'Mô hình Qwen2.5-14B đang xử lý',
    Icon: Brain,
    color: 'text-violet-400',
    ringColor: 'ring-violet-500/40 bg-violet-500/10',
  },
  {
    key: 'searching',
    label: 'Tra cứu dữ liệu',
    sublabel: 'Grade_Search_Tool → CSV data',
    Icon: Search,
    color: 'text-cyan-400',
    ringColor: 'ring-cyan-500/40 bg-cyan-500/10',
  },
  {
    key: 'analyzing',
    label: 'Phân tích điểm số',
    sublabel: 'Score_Analyzer + Learning_Gap_Detector',
    Icon: BarChart3,
    color: 'text-amber-400',
    ringColor: 'ring-amber-500/40 bg-amber-500/10',
  },
  {
    key: 'generating',
    label: 'Tổng hợp phản hồi',
    sublabel: 'Định dạng Markdown & kiểm tra output',
    Icon: Wand2,
    color: 'text-indigo-400',
    ringColor: 'ring-indigo-500/40 bg-indigo-500/10',
  },
];

const STEP_ORDER: LoadingStep[] = ['validating', 'thinking', 'searching', 'analyzing', 'generating'];

function AgentProgressIndicator({ currentStep }: { currentStep: LoadingStep }) {
  const currentIndex = STEP_ORDER.indexOf(currentStep);

  return (
    <div className="flex w-full gap-4 py-5 px-4 bg-[#0f1422]/40 border-y border-slate-800/50">
      {/* Avatar */}
      <div className="flex-shrink-0">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-violet-600 to-indigo-600 border border-violet-400/20 flex items-center justify-center text-white shadow-lg shadow-violet-500/10">
          <Sparkles className="w-5 h-5 fill-white/20 animate-pulse" />
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 flex flex-col gap-3 min-w-0">
        <span className="text-xs font-semibold text-slate-300 select-none">EduTrace AI · Đang xử lý</span>

        {/* Progress bar */}
        <div className="flex items-center gap-1.5">
          {STEPS.map((step, idx) => {
            const isDone = idx < currentIndex;
            const isActive = idx === currentIndex;
            return (
              <div
                key={step.key}
                className={`h-1 flex-1 rounded-full transition-all duration-700 ${
                  isDone
                    ? 'bg-violet-500'
                    : isActive
                    ? 'bg-violet-400 animate-pulse'
                    : 'bg-slate-700/60'
                }`}
              />
            );
          })}
        </div>

        {/* Step list */}
        <div className="flex flex-col gap-1.5">
          {STEPS.map((step, idx) => {
            const isDone = idx < currentIndex;
            const isActive = idx === currentIndex;
            const { Icon } = step;

            if (!isActive && !isDone) return null;

            return (
              <div
                key={step.key}
                className={`flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg transition-all duration-500 ${
                  isActive ? `ring-1 ${step.ringColor}` : 'opacity-50'
                }`}
              >
                {isDone ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                ) : (
                  <Icon className={`w-4 h-4 flex-shrink-0 ${step.color} ${isActive ? 'animate-pulse' : ''}`} />
                )}
                <div className="flex flex-col min-w-0">
                  <span className={`text-xs font-medium leading-tight ${isActive ? 'text-slate-200' : 'text-slate-500'}`}>
                    {step.label}
                  </span>
                  {isActive && (
                    <span className="text-[10px] text-slate-500 leading-tight mt-0.5">{step.sublabel}</span>
                  )}
                </div>
                {isActive && (
                  <div className="ml-auto flex items-center gap-0.5 flex-shrink-0">
                    <span className="w-1.5 h-1.5 rounded-full bg-violet-400 animate-bounce" style={{ animationDelay: '0ms' }} />
                    <span className="w-1.5 h-1.5 rounded-full bg-violet-400 animate-bounce" style={{ animationDelay: '120ms' }} />
                    <span className="w-1.5 h-1.5 rounded-full bg-violet-400 animate-bounce" style={{ animationDelay: '240ms' }} />
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Estimated time note */}
        <p className="text-[10px] text-slate-600 select-none">
          ⏱ Thời gian xử lý tối đa ~60s/lần gọi · Tối đa 5 vòng Agent Loop
        </p>
      </div>
    </div>
  );
}

export const ChatBox: React.FC = () => {
  const { activeSession, isLoading, loadingStep } = useChat();
  const { sendMessage } = useChatStream();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const promptCards = [
    {
      icon: <GraduationCap className="w-5 h-5 text-violet-400" />,
      title: "Tra cứu điểm TOEIC",
      description: "Xem điểm 4 kỹ năng Listening, Reading, Speaking, Writing.",
      prompt: "Cho tôi xem điểm TOEIC của học sinh SV001."
    },
    {
      icon: <BarChart3 className="w-5 h-5 text-amber-400" />,
      title: "Phân tích điểm mạnh/yếu",
      description: "Phân tích chi tiết và đề xuất kế hoạch cải thiện.",
      prompt: "Phân tích điểm mạnh điểm yếu của học sinh SV002 và lập lộ trình ôn luyện 4 tuần."
    },
    {
      icon: <Terminal className="w-5 h-5 text-emerald-400" />,
      title: "Tổng hợp lớp học",
      description: "Xem tổng quan điểm số toàn lớp theo từng kỹ năng.",
      prompt: "Hãy cho tôi xem và so sánh điểm TOEIC của các học sinh SV001, SV002, SV003."
    },
    {
      icon: <MessageSquare className="w-5 h-5 text-cyan-400" />,
      title: "Lộ trình học cá nhân",
      description: "Tạo kế hoạch ôn tập cá nhân hóa dựa trên điểm số thực tế.",
      prompt: "Dựa trên kết quả thi của học sinh SV003, hãy lập kế hoạch ôn tập cá nhân hóa trong 2 tuần."
    }
  ];

  // Scroll to bottom whenever messages list or loading state changes
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [activeSession?.messages?.length, isLoading]);

  const messages = activeSession?.messages || [];

  return (
    <div className="flex-1 overflow-y-auto custom-scrollbar flex flex-col bg-[#080b13]">
      {messages.length === 0 ? (
        /* Empty State Landing page */
        <div className="flex-1 flex flex-col items-center justify-center max-w-3xl mx-auto px-6 py-12 select-none">
          <div className="flex flex-col items-center text-center gap-3.5 mb-10">
            <div className="p-3 bg-violet-600/10 border border-violet-500/30 rounded-2xl text-violet-400 shadow-lg shadow-violet-500/5">
              <Sparkles className="w-8 h-8 fill-violet-400/20" />
            </div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-violet-400 via-indigo-200 to-cyan-300 bg-clip-text text-transparent tracking-tight">
              EduTrace Chatbot MVP
            </h1>
            <p className="text-sm text-slate-400 max-w-md leading-relaxed">
              Trợ lý AI tra cứu điểm TOEIC và lập lộ trình học tập cá nhân hóa. Bắt đầu bằng cách chọn một gợi ý bên dưới!
            </p>
          </div>

          {/* Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full">
            {promptCards.map((card, idx) => (
              <div
                key={idx}
                onClick={() => sendMessage(card.prompt)}
                className="group p-5 bg-[#0f1424]/40 hover:bg-[#12192e]/60 border border-slate-800/60 hover:border-violet-500/40 rounded-2xl cursor-pointer transition-all duration-300 transform hover:-translate-y-1 shadow-md shadow-slate-950/20"
              >
                <div className="flex gap-4 items-start">
                  <div className="p-2.5 bg-slate-900/80 border border-slate-800 rounded-xl flex-shrink-0 group-hover:scale-110 transition-transform duration-300">
                    {card.icon}
                  </div>
                  <div className="flex flex-col gap-1 overflow-hidden flex-1">
                    <span className="text-sm font-semibold text-slate-200 group-hover:text-violet-400 transition-colors duration-200 truncate">
                      {card.title}
                    </span>
                    <span className="text-xs text-slate-400 leading-relaxed">
                      {card.description}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        /* Messages List */
        <div className="flex flex-col flex-1 py-4">
          {messages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))}

          {/* Agent Progress Indicator */}
          {isLoading && messages.length > 0 && messages[messages.length - 1].role === 'user' && loadingStep !== 'idle' && (
            <AgentProgressIndicator currentStep={loadingStep} />
          )}
          <div ref={messagesEndRef} />
        </div>
      )}
    </div>
  );
};
