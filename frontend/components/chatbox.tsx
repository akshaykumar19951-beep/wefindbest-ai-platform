"use client";

import { useState } from "react";
import { sendChat } from "@/lib/api";

type Message = {
  role: "user" | "assistant";
  content: string;
};

export default function ChatBox() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [apiKey, setApiKey] = useState(() =>
    typeof window === "undefined" ? "" : localStorage.getItem("wefindbest_api_key") || "",
  );
  const [loading, setLoading] = useState(false);

  const saveApiKey = (value: string) => {
    setApiKey(value);
    if (typeof window !== "undefined") {
      localStorage.setItem("wefindbest_api_key", value);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    if (!apiKey.trim()) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Add your API key before sending a chat request." },
      ]);
      return;
    }

    const userMessage = input;
    setInput("");
    setLoading(true);
    setMessages((prev) => [
      ...prev,
      { role: "user", content: userMessage },
      { role: "assistant", content: "Thinking..." },
    ]);

    try {
      const data = await sendChat(userMessage, apiKey);

      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: "assistant",
          content: data.response,
        };
        return updated;
      });
    } catch (err) {
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: "assistant",
          content: err instanceof Error ? err.message : "Error connecting to backend",
        };
        return updated;
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-zinc-200 bg-white px-4 py-3">
        <label className="block text-xs font-medium uppercase tracking-wide text-zinc-500">
          API key
        </label>
        <input
          className="mt-1 w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm outline-none focus:border-zinc-900"
          value={apiKey}
          onChange={(e) => saveApiKey(e.target.value)}
          placeholder="Paste your x-api-key"
        />
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto px-4 py-6">
        {messages.length === 0 && (
          <div className="text-sm text-zinc-500">
            Send a message to test your local AI API.
          </div>
        )}

        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[78%] rounded-md px-4 py-2 text-sm whitespace-pre-wrap ${
                m.role === "user" ? "bg-zinc-950 text-white" : "bg-zinc-100 text-zinc-900"
              }`}
            >
              {m.content}
            </div>
          </div>
        ))}
      </div>

      <div className="flex gap-2 border-t border-zinc-200 bg-white p-4">
        <input
          className="flex-1 rounded-md border border-zinc-300 bg-white px-4 py-2 text-sm outline-none focus:border-zinc-900"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          placeholder="Ask something..."
        />

        <button
          onClick={sendMessage}
          disabled={loading}
          className="rounded-md bg-zinc-950 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {loading ? "Sending" : "Send"}
        </button>
      </div>
    </div>
  );
}
