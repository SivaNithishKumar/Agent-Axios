import { Bot, User } from "lucide-react";
import { cn } from "@/lib/utils";

type Message = {
  id: number;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
};

interface ChatMessageProps {
  message: Message;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isAssistant = message.role === "assistant";

  return (
    <div
      className={cn(
        "flex gap-4 animate-fade-in",
        isAssistant ? "justify-start" : "justify-end"
      )}
    >
      {isAssistant && (
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-accent flex items-center justify-center flex-shrink-0">
          <Bot className="w-5 h-5 text-primary-foreground" />
        </div>
      )}

      <div
        className={cn(
          "max-w-[80%] rounded-2xl p-4 shadow-[var(--shadow-soft)]",
          isAssistant
            ? "bg-card border border-border"
            : "bg-primary text-primary-foreground"
        )}
      >
        <div className="prose prose-sm max-w-none">
          <p className="m-0 whitespace-pre-wrap">{message.content}</p>
        </div>
        <div
          className={cn(
            "text-xs mt-2 opacity-70",
            isAssistant ? "text-muted-foreground" : "text-primary-foreground"
          )}
        >
          {message.timestamp.toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </div>
      </div>

      {!isAssistant && (
        <div className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center flex-shrink-0">
          <User className="w-5 h-5 text-foreground" />
        </div>
      )}
    </div>
  );
}
