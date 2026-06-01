'use client';

import React from 'react';
import { ChatProvider, useChat } from '../../store/chatContext';
import { Sidebar } from '../../components/chat/Sidebar';
import { ChatBox } from '../../components/chat/ChatBox';
import { ChatInput } from '../../components/chat/ChatInput';
import { PanelLeftOpen } from 'lucide-react';

const ChatClientContent: React.FC = () => {
  const { isSidebarOpen, toggleSidebar } = useChat();

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#080b13] text-slate-100 font-sans">
      {/* 1. Left Sidebar */}
      <Sidebar />

      {/* 2. Main Chat Area */}
      <main className="flex-1 flex flex-col h-full relative overflow-hidden">
        {/* Toggle Sidebar Button (visible only when sidebar is closed) */}
        {!isSidebarOpen && (
          <div className="absolute top-4 left-4 z-10 select-none">
            <button
              onClick={toggleSidebar}
              className="p-2.5 bg-[#0f1424]/80 border border-slate-800 hover:border-slate-700/80 text-slate-300 hover:text-slate-100 rounded-xl backdrop-blur-md transition-all duration-300 shadow-md shadow-slate-950/20"
              title="Mở sidebar"
            >
              <PanelLeftOpen className="w-5 h-5" />
            </button>
          </div>
        )}

        {/* Header / Title bar */}
        <div className="h-14 border-b border-slate-800/40 bg-[#080b13]/80 flex items-center justify-center select-none flex-shrink-0 z-5">
          <span className="text-xs font-semibold text-slate-400 tracking-wider">
            Active Session: mimo-v2.5-pro LLM
          </span>
        </div>

        {/* Chat List Scroll View */}
        <ChatBox />

        {/* Chat Input Text Area */}
        <ChatInput />
      </main>
    </div>
  );
};

export default function ChatPage() {
  return (
    <ChatProvider>
      <ChatClientContent />
    </ChatProvider>
  );
}
