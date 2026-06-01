'use client';

import React from 'react';
import { useChat } from '../../store/chatContext';
import { Button } from '../common/Button';
import { MessageSquarePlus, MessageSquare, Trash2, BarChart3, PanelLeftClose, Zap } from 'lucide-react';
import { formatDate } from '../../utils/format';

export const Sidebar: React.FC = () => {
  const {
    sessions,
    activeSessionId,
    isSidebarOpen,
    createNewSession,
    deleteSession,
    setActiveSessionId,
    toggleSidebar
  } = useChat();

  if (!isSidebarOpen) return null;

  return (
    <aside className="w-80 h-full bg-[#0b0f19] border-r border-slate-800/80 flex flex-col z-20 transition-all duration-300">
      {/* Sidebar Header */}
      <div className="p-4 border-b border-slate-800/60 flex items-center justify-between">
        <div className="flex items-center gap-2 select-none">
          <div className="p-1.5 bg-violet-600/10 border border-violet-500/30 rounded-lg text-violet-400">
            <Zap className="w-5 h-5 fill-violet-400/20" />
          </div>
          <span className="font-semibold text-slate-100 text-sm tracking-wide uppercase">Mimo Chatbot</span>
        </div>
        <button
          onClick={toggleSidebar}
          className="p-2 hover:bg-white/5 text-slate-400 hover:text-slate-200 rounded-lg transition-colors duration-200"
          title="Đóng sidebar"
        >
          <PanelLeftClose className="w-4 h-4" />
        </button>
      </div>

      {/* New Chat Button */}
      <div className="p-4">
        <Button
          onClick={() => createNewSession()}
          variant="primary"
          className="w-full justify-start text-xs font-semibold py-3 gap-2"
        >
          <MessageSquarePlus className="w-4 h-4" />
          Tạo cuộc hội thoại mới
        </Button>
      </div>

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto px-3 pb-4 space-y-1.5 custom-scrollbar">
        <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider px-3 mb-2 select-none">
          Lịch sử trò chuyện
        </div>
        {sessions.length === 0 ? (
          <div className="text-xs text-slate-500 text-center py-8 select-none px-4 itlaic bg-slate-900/10 rounded-xl border border-slate-900/5">
            Chưa có cuộc trò chuyện nào
          </div>
        ) : (
          sessions.map((session) => {
            const isActive = session.id === activeSessionId;
            return (
              <div
                key={session.id}
                onClick={() => setActiveSessionId(session.id)}
                className={`group flex items-center justify-between p-3 rounded-xl cursor-pointer transition-all duration-300 select-none ${
                  isActive
                    ? 'bg-violet-600/10 text-violet-300 border border-violet-500/20 shadow-inner'
                    : 'text-slate-400 hover:bg-white/5 hover:text-slate-200 border border-transparent'
                }`}
              >
                <div className="flex items-center gap-2.5 overflow-hidden flex-1">
                  <MessageSquare className={`w-4 h-4 flex-shrink-0 ${isActive ? 'text-violet-400' : 'text-slate-500'}`} />
                  <div className="flex flex-col overflow-hidden flex-1">
                    <span className="text-xs font-medium truncate leading-normal">
                      {session.title}
                    </span>
                    <span className="text-[9px] text-slate-500/80 mt-0.5">
                      {formatDate(session.createdAt)}
                    </span>
                  </div>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteSession(session.id);
                  }}
                  className="opacity-0 group-hover:opacity-100 p-1 text-slate-500 hover:text-red-400 hover:bg-red-500/10 rounded-md transition-all duration-200"
                  title="Xóa cuộc trò chuyện"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            );
          })
        )}
      </div>

      {/* Sidebar Footer */}
      <div className="p-4 border-t border-slate-800/60 bg-[#070a11]/40 flex flex-col gap-2">
        <a
          href="http://127.0.0.1:8000/api/metrics"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 px-3 py-2.5 text-xs text-slate-400 hover:text-slate-200 hover:bg-white/5 rounded-xl border border-slate-800/30 transition-all duration-300 select-none"
        >
          <BarChart3 className="w-4 h-4 text-violet-400" />
          <span>Báo cáo hiệu năng API</span>
        </a>
        <div className="flex items-center justify-between text-[10px] text-slate-500 px-1 mt-1 select-none">
          <span>Trạng thái máy chủ:</span>
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
            <span className="text-emerald-400 font-medium">Hoạt động</span>
          </div>
        </div>
      </div>
    </aside>
  );
};
