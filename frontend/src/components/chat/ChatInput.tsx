'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useChat } from '../../store/chatContext';
import { useChatStream } from '../../hooks/useChatStream';
import { SendHorizontal } from 'lucide-react';

export const ChatInput: React.FC = () => {
  const { isLoading } = useChat();
  const { sendMessage } = useChatStream();
  const [input, setInput] = useState<string>('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea height as user types
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 180)}px`;
    }
  }, [input]);

  const handleSend = () => {
    if (!input.trim() || isLoading) return;
    sendMessage(input);
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="p-4 bg-[#080b13] border-t border-slate-800/40">
      <div className="max-w-3xl mx-auto relative flex items-end bg-[#0f1424]/40 border border-slate-800 hover:border-slate-700/80 rounded-2xl p-1.5 focus-within:border-violet-500/80 focus-within:ring-1 focus-within:ring-violet-500/20 transition-all duration-300">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Hỏi gì đó với MiMo AI..."
          rows={1}
          disabled={isLoading}
          className="flex-1 max-h-[180px] bg-transparent text-slate-100 placeholder-slate-500 text-sm py-3 px-3.5 focus:outline-none resize-none overflow-y-auto custom-scrollbar leading-relaxed"
        />
        <div className="flex items-center justify-end px-2 pb-1.5 flex-shrink-0 select-none">
          <button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            className={`p-2.5 rounded-xl flex items-center justify-center transition-all duration-300 transform active:scale-95 ${input.trim() && !isLoading
                ? 'bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white shadow-md shadow-indigo-500/20'
                : 'bg-[#181f30] text-slate-600 border border-slate-800/40 cursor-not-allowed'
              }`}
            title="Gửi tin nhắn"
          >
            <SendHorizontal className="w-4 h-4" />
          </button>
        </div>
      </div>
      <div className="max-w-3xl mx-auto text-center mt-2 select-none">
        <span className="text-[10px] text-slate-500/80 leading-normal">
          EduTrace AI có thể mắc sai sót. Vui lòng xác minh thông tin quan trọng.
        </span>
      </div>
    </div>
  );
};
