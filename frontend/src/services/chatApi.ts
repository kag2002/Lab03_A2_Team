import { ChatResponse, Message } from "../types/chat";

const API_BASE = "http://127.0.0.1:8000/api";

export async function sendChatMessage(messages: Message[], temperature: number = 0.7): Promise<ChatResponse> {
  const payload = {
    messages: messages.map(m => ({
      role: m.role,
      content: m.content
    })),
    temperature
  };

  const response = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `HTTP Error ${response.status}`);
  }

  return response.json();
}
