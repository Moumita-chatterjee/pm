import { API_BASE_URL } from "@/lib/api-base";
import type { BoardData } from "@/lib/kanban";

export const me = () =>
  fetch(`${API_BASE_URL}/api/me`, { credentials: "include" });

export const login = (username: string, password: string) =>
  fetch(`${API_BASE_URL}/api/login`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });

export const logout = () =>
  fetch(`${API_BASE_URL}/api/logout`, {
    method: "POST",
    credentials: "include",
  });

export const getBoard = async (): Promise<BoardData> => {
  const response = await fetch(`${API_BASE_URL}/api/board`, {
    credentials: "include",
  });
  return response.json();
};

export const putBoard = async (board: BoardData): Promise<BoardData> => {
  const response = await fetch(`${API_BASE_URL}/api/board`, {
    method: "PUT",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(board),
  });
  return response.json();
};

export type ChatMessage = { role: "user" | "assistant"; content: string };

export type ChatResponse = { reply: string; board: BoardData };

export const chat = async (
  message: string,
  history: ChatMessage[]
): Promise<ChatResponse> => {
  const response = await fetch(`${API_BASE_URL}/api/chat`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, history }),
  });
  return response.json();
};
