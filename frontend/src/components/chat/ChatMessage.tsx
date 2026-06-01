import React from 'react';
import { Message } from '../../types/chat';
import { Bot, User, Cpu, Clock, Layers } from 'lucide-react';
import { formatTime } from '../../utils/format';

interface ChatMessageProps {
  message: Message;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isBot = message.role === 'assistant';

  // Quick custom formatter for simple Markdown elements (bold, lists, inline code, line breaks)
  const renderMessageContent = (content: string) => {
    if (!content) return null;

    // Split into paragraphs / lines
    const lines = content.split('\n');
    return lines.map((line, idx) => {
      // Check for bullet lists
      if (line.trim().startsWith('-') || line.trim().startsWith('*')) {
        const item = line.replace(/^[-*]\s+/, '');
        return (
          <li key={idx} className="ml-4 list-disc text-sm text-slate-200 leading-relaxed my-0.5">
            {parseInlineFormatting(item)}
          </li>
        );
      }
      return (
        <p key={idx} className="text-sm text-slate-200 leading-relaxed min-h-[1.25rem] my-1">
          {parseInlineFormatting(line)}
        </p>
      );
    });
  };

  const parseInlineFormatting = (text: string) => {
    // Basic regex parser for **bold** and `code`
    const boldRegex = /\*\*(.*?)\*\*/g;
    const codeRegex = /`(.*?)`/g;

    const elements: React.ReactNode[] = [];
    const boldParts = text.split(boldRegex);

    boldParts.forEach((part, i) => {
      if (i % 2 === 1) {
        elements.push(<strong key={`b-${i}`} className="font-semibold text-violet-400">{part}</strong>);
      } else {
        // Parse inline code inside plain text parts
        const codeParts = part.split(codeRegex);
        codeParts.forEach((cPart, j) => {
          if (j % 2 === 1) {
            elements.push(
              <code key={`c-${i}-${j}`} className="px-1.5 py-0.5 bg-[#070b13] border border-slate-800 text-pink-400 font-mono text-[11px] rounded-md">
                {cPart}
              </code>
            );
          } else {
            elements.push(cPart);
          }
        });
      }
    });

    return elements;
  };

  // Calculations for Telemetry badge
  const showTelemetry = isBot && message.latency_ms && message.total_tokens;
  const tokSec = showTelemetry ? ((message.total_tokens || 0) / ((message.latency_ms || 1) / 1000)).toFixed(1) : '0';
  const latencySec = showTelemetry ? ((message.latency_ms || 0) / 1000).toFixed(2) : '0';

  return (
    <div className={`flex w-full gap-4 py-4 px-4 transition-all duration-300 ${isBot ? 'bg-[#0f1422]/30 border-y border-slate-900/50' : 'bg-transparent'
      }`}>
      {/* Avatar Container */}
      <div className="flex-shrink-0">
        {isBot ? (
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-violet-600 to-indigo-600 border border-violet-400/20 flex items-center justify-center text-white shadow-md shadow-violet-500/10">
            <Bot className="w-5 h-5" />
          </div>
        ) : (
          <div className="w-9 h-9 rounded-xl bg-[#1e293b] border border-slate-700/60 flex items-center justify-center text-slate-300">
            <User className="w-5 h-5" />
          </div>
        )}
      </div>

      {/* Message Content Area */}
      <div className="flex-1 flex flex-col gap-1.5 overflow-hidden">
        {/* Name and Time */}
        <div className="flex items-center gap-2 select-none">
          <span className="text-xs font-semibold text-slate-300">
            {isBot ? 'EduTrace AI' : 'Bạn'}
          </span>
          <span className="text-[10px] text-slate-500">
            {formatTime(message.timestamp)}
          </span>
        </div>

        {/* Text Body */}
        <div className="flex flex-col select-text">
          {renderMessageContent(message.content)}
        </div>

        {/* Telemetry Badge */}
        {showTelemetry && (
          <div className="flex flex-wrap gap-2 mt-3 select-none">
            <div className="inline-flex items-center gap-3.5 px-3 py-1.5 bg-[#0b0f19]/80 border border-slate-800/80 text-[10px] text-slate-400 rounded-full font-mono shadow-sm">
              <div className="flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5 text-violet-400 animate-pulse" />
                <span><strong className="text-slate-200">{tokSec}</strong> tok/s</span>
              </div>
              <div className="w-px h-2.5 bg-slate-800"></div>
              <div className="flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-indigo-400" />
                <span><strong className="text-slate-200">{latencySec}</strong>s</span>
              </div>
              <div className="w-px h-2.5 bg-slate-800"></div>
              <div className="flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-cyan-400" />
                <span><strong className="text-slate-200">{message.total_tokens}</strong> tokens</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
