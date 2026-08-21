"use client";

import { useEffect, useState } from "react";
import { KanbanBoard } from "@/components/KanbanBoard";
import { LoginForm } from "@/components/LoginForm";
import { getBoard, logout, me } from "@/lib/api";
import type { BoardData } from "@/lib/kanban";

type AuthStatus = "loading" | "anon" | "authed";

export default function Home() {
  const [status, setStatus] = useState<AuthStatus>("loading");
  const [board, setBoard] = useState<BoardData | null>(null);

  useEffect(() => {
    me().then((response) => {
      setStatus(response.ok ? "authed" : "anon");
    });
  }, []);

  useEffect(() => {
    if (status === "authed") {
      getBoard().then(setBoard);
    }
  }, [status]);

  const handleLogout = async () => {
    await logout();
    setStatus("anon");
    setBoard(null);
  };

  if (status === "loading") {
    return null;
  }

  if (status === "anon") {
    return <LoginForm onSuccess={() => setStatus("authed")} />;
  }

  return (
    <div>
      <div className="mx-auto flex max-w-[1500px] justify-end px-6 pt-4">
        <button
          type="button"
          onClick={handleLogout}
          className="rounded-full border border-[var(--stroke)] px-4 py-2 text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)] transition hover:text-[var(--navy-dark)]"
        >
          Log out
        </button>
      </div>
      {board && <KanbanBoard board={board} setBoard={setBoard} />}
    </div>
  );
}
