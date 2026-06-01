export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  latency_ms?: number;
  prompt_tokens?: number;
  completion_tokens?: number;
  total_tokens?: number;
}

export interface Session {
  id: string;
  title: string;
  messages: Message[];
  createdAt: string;
}

export interface ChatResponseUsage {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
}

export interface ChatResponse {
  reply: string;
  model: string;
  usage: ChatResponseUsage;
  latency_ms: number;
}
