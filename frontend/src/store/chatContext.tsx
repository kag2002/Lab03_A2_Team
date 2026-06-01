'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { Message, Session } from '../types/chat';
import { useLocalStorage } from '../hooks/useLocalStorage';

interface ChatContextType {
  sessions: Session[];
  activeSessionId: string | null;
  activeSession: Session | null;
  isLoading: boolean;
  isSidebarOpen: boolean;
  createNewSession: () => string;
  deleteSession: (id: string) => void;
  setActiveSessionId: (id: string) => void;
  updateSessionMessages: (sessionId: string, messages: Message[]) => void;
  setIsLoading: (loading: boolean) => void;
  toggleSidebar: () => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const ChatProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [sessions, setSessions] = useLocalStorage<Session[]>('chatbot_sessions', []);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState<boolean>(true);

  // Set the first session as active if none is selected
  useEffect(() => {
    if (sessions.length > 0 && activeSessionId === null) {
      setActiveSessionId(sessions[0].id);
    }
  }, [sessions, activeSessionId]);

  const createNewSession = (): string => {
    const newSession: Session = {
      id: crypto.randomUUID(),
      title: `Hội thoại mới`,
      messages: [],
      createdAt: new Date().toISOString(),
    };
    setSessions([newSession, ...sessions]);
    setActiveSessionId(newSession.id);
    return newSession.id;
  };

  const deleteSession = (id: string) => {
    const updatedSessions = sessions.filter((s) => s.id !== id);
    setSessions(updatedSessions);
    if (activeSessionId === id) {
      setActiveSessionId(updatedSessions.length > 0 ? updatedSessions[0].id : null);
    }
  };

  const updateSessionMessages = (sessionId: string, messages: Message[]) => {
    setSessions((prevSessions) =>
      prevSessions.map((session) => {
        if (session.id !== sessionId) return session;

        // Auto-generate title from the first user message if it's currently default
        let title = session.title;
        if (session.title === 'Hội thoại mới' && messages.length > 0) {
          const firstUserMessage = messages.find((m) => m.role === 'user');
          if (firstUserMessage) {
            title = firstUserMessage.content.slice(0, 30) + (firstUserMessage.content.length > 30 ? '...' : '');
          }
        }

        return { ...session, messages, title };
      })
    );
  };

  const toggleSidebar = () => setIsSidebarOpen((prev) => !prev);

  const activeSession = sessions.find((s) => s.id === activeSessionId) || null;

  return (
    <ChatContext.Provider
      value={{
        sessions,
        activeSessionId,
        activeSession,
        isLoading,
        isSidebarOpen,
        createNewSession,
        deleteSession,
        setActiveSessionId,
        updateSessionMessages,
        setIsLoading,
        toggleSidebar,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
};

export const useChat = () => {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
};
