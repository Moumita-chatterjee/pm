"use client";

import { useState, type FormEvent } from "react";
import { chat, type ChatMessage } from "@/lib/api";
import type { BoardData } from "@/lib/kanban";

type ChatSidebarProps = {
  onBoardUpdate: (board: BoardData) => void;
};

export const ChatSidebar = ({ onBoardUpdate }: ChatSidebarProps) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const message = input.trim();
    if (!message || isSending) {
      return;
    }

    const history = messages;
    setMessages([...history, { role: "user", content: message }]);
    setInput("");
    setIsSending(true);

    try {
      const response = await chat(message, history);
      setMessages((current) => [
        ...current,
        { role: "assistant", content: response.reply },
      ]);
      onBoardUpdate(response.board);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <aside className="flex h-fit flex-col rounded-[32px] border border-[var(--stroke)] bg-white/80 p-6 shadow-[var(--shadow)] backdrop-blur lg:sticky lg:top-6">
      <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[var(--gray-text)]">
        AI Assistant
      </p>
      <h2 className="mt-2 font-display text-lg font-semibold text-[var(--navy-dark)]">
        Chat with your board
      </h2>

      <div className="mt-4 flex max-h-[420px] min-h-[160px] flex-col gap-3 overflow-y-auto">
        {messages.length === 0 && (
          <p className="text-sm text-[var(--gray-text)]">
            Ask me to create, edit, or move cards.
          </p>
        )}
        {messages.map((message, index) => (
          <div
            key={index}
            data-testid={`chat-message-${message.role}`}
            className={
              message.role === "user"
                ? "self-end rounded-2xl bg-[var(--primary-blue)] px-3 py-2 text-sm text-white"
                : "self-start rounded-2xl bg-[var(--surface)] px-3 py-2 text-sm text-[var(--navy-dark)]"
            }
          >
            {message.content}
          </div>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="mt-4 flex gap-2">
        <input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Ask the AI assistant..."
          aria-label="Chat message"
          className="flex-1 rounded-xl border border-[var(--stroke)] bg-white px-3 py-2 text-sm font-medium text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
          disabled={isSending}
        />
        <button
          type="submit"
          disabled={isSending || !input.trim()}
          className="rounded-full bg-[var(--secondary-purple)] px-4 py-2 text-xs font-semibold uppercase tracking-wide text-white transition hover:brightness-110 disabled:opacity-60"
        >
          Send
        </button>
      </form>
    </aside>
  );
};
