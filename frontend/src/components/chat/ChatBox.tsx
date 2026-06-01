'use client';

import React, { useRef, useEffect } from 'react';
import { useChat } from '../../store/chatContext';
import { ChatMessage } from './ChatMessage';
import { useChatStream } from '../../hooks/useChatStream';
import { Sparkles, MessageSquare, Terminal, Lightbulb, GraduationCap } from 'lucide-react';

export const ChatBox: React.FC = () => {
  const { activeSession, isLoading } = useChat();
  const { sendMessage } = useChatStream();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const promptCards = [
    {
      icon: <GraduationCap className="w-5 h-5 text-violet-400" />,
      title: "Giải thích Đệ quy",
      description: "Giải thích khái niệm đệ quy một cách dễ hiểu kèm ví dụ minh họa.",
      prompt: "Hãy giải thích đệ quy trong lập trình một cách thật dễ hiểu cho người mới bắt đầu và cho ví dụ minh họa."
    },
    {
      icon: <Lightbulb className="w-5 h-5 text-amber-400" />,
      title: "Ý tưởng khởi nghiệp",
      description: "Brainstorm các ý tưởng ứng dụng AI hỗ trợ học sinh sinh viên.",
      prompt: "Hãy giúp tôi brainstorm 5 ý tưởng khởi nghiệp sáng tạo ứng dụng AI để hỗ trợ học sinh, sinh viên trong việc tự học."
    },
    {
      icon: <Terminal className="w-5 h-5 text-emerald-400" />,
      title: "Tạo cấu trúc SQL",
      description: "Thiết kế cơ sở dữ liệu cho một ứng dụng mạng xã hội thu nhỏ.",
      prompt: "Hãy thiết kế cấu trúc các bảng SQL cho một ứng dụng mạng xã hội thu nhỏ (bao gồm Users, Posts, Comments, Likes) kèm khoá chính/ngoại."
    },
    {
      icon: <MessageSquare className="w-5 h-5 text-cyan-400" />,
      title: "Viết email chuyên nghiệp",
      description: "Soạn thảo email gửi sếp xin nghỉ phép ngắn ngày.",
      prompt: "Hãy soạn giúp tôi một email xin nghỉ phép 2 ngày gửi cho sếp một cách chuyên nghiệp, lịch sự nhưng ngắn gọn."
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
              Mimo Chatbot MVP
            </h1>
            <p className="text-sm text-slate-400 max-w-md leading-relaxed">
              Trải nghiệm mô hình thông minh **MiMo-v2.5-pro** với 1 nghìn tỷ tham số. Bắt đầu cuộc hội thoại bằng cách chọn một chủ đề gợi ý bên dưới!
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

          {/* Pulsing loading state */}
          {isLoading && messages.length > 0 && messages[messages.length - 1].role === 'user' && (
            <div className="flex w-full gap-4 py-4 px-4 bg-[#0f1422]/30 border-y border-slate-900/50">
              <div className="flex-shrink-0">
                <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-violet-600 to-indigo-600 border border-violet-400/20 flex items-center justify-center text-white animate-pulse">
                  <Sparkles className="w-5 h-5 fill-white/20" />
                </div>
              </div>
              <div className="flex-1 flex flex-col gap-2">
                <span className="text-xs font-semibold text-slate-300 select-none">MiMo AI</span>
                <div className="flex items-center gap-1.5 py-1">
                  <span className="w-2.5 h-2.5 rounded-full bg-violet-500 animate-bounce" style={{ animationDelay: '0ms' }}></span>
                  <span className="w-2.5 h-2.5 rounded-full bg-violet-500 animate-bounce" style={{ animationDelay: '150ms' }}></span>
                  <span className="w-2.5 h-2.5 rounded-full bg-violet-500 animate-bounce" style={{ animationDelay: '300ms' }}></span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      )}
    </div>
  );
};
