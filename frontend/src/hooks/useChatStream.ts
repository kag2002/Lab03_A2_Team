'use client';

import { useChat } from '../store/chatContext';
import { sendChatMessage } from '../services/chatApi';
import { Message } from '../types/chat';

export function useChatStream() {
  const { activeSession, activeSessionId, createNewSession, updateSessionMessages, setIsLoading } = useChat();

  const sendMessage = async (content: string) => {
    if (!content.trim()) return;

    let currentSessionId = activeSessionId;
    let currentMessages = activeSession ? [...activeSession.messages] : [];

    // If there is no active session, create one first
    if (!currentSessionId) {
      currentSessionId = createNewSession();
      currentMessages = [];
    }

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: content.trim(),
      timestamp: new Date().toISOString(),
    };

    const updatedMessages = [...currentMessages, userMessage];
    updateSessionMessages(currentSessionId, updatedMessages);
    setIsLoading(true);

    try {
      // Call backend API
      const response = await sendChatMessage(updatedMessages);
      
      const assistantMessageId = crypto.randomUUID();
      const fullReply = response.reply;
      
      // Initialize assistant message
      const assistantMessage: Message = {
        id: assistantMessageId,
        role: 'assistant',
        content: '',
        timestamp: new Date().toISOString(),
        latency_ms: response.latency_ms,
        prompt_tokens: response.usage.prompt_tokens,
        completion_tokens: response.usage.completion_tokens,
        total_tokens: response.usage.total_tokens,
      };

      const messagesWithAssistantPlaceholder = [...updatedMessages, assistantMessage];
      updateSessionMessages(currentSessionId!, messagesWithAssistantPlaceholder);

      // Simulate streaming typing effect
      let typedContent = '';
      const typingSpeed = 8; // ms per char
      let charIndex = 0;

      const typeNextChar = () => {
        if (charIndex < fullReply.length) {
          typedContent += fullReply[charIndex];
          const typedMessages = messagesWithAssistantPlaceholder.map(m => 
            m.id === assistantMessageId ? { ...m, content: typedContent } : m
          );
          updateSessionMessages(currentSessionId!, typedMessages);
          charIndex++;
          setTimeout(typeNextChar, typingSpeed);
        } else {
          setIsLoading(false);
        }
      };

      typeNextChar();

    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: 'Đã xảy ra lỗi khi kết nối với máy chủ AI. Vui lòng kiểm tra xem backend đã được khởi động thành công ở cổng 8000 chưa.',
        timestamp: new Date().toISOString(),
      };
      updateSessionMessages(currentSessionId!, [...updatedMessages, errorMessage]);
      setIsLoading(false);
    }
  };

  return { sendMessage };
}
