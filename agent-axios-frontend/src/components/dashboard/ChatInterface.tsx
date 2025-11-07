import { useState, useRef, useEffect } from "react";
import { Send, Sparkles, GitBranch, FileText, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ChatMessage } from "./ChatMessage";
import { AnalysisProgress } from "./AnalysisProgress";
import { toast } from "sonner";

type Message = {
  id: number;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
};

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      role: "assistant",
      content: "👋 Welcome! I'm your AI-powered CVE analysis assistant. Paste a GitHub repository URL to get started with a comprehensive security analysis.",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollElement = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]');
      if (scrollElement) {
        scrollElement.scrollTop = scrollElement.scrollHeight;
      }
    }
  }, [messages, isAnalyzing]);

  const handleSend = () => {
    if (!input.trim() || isAnalyzing) return;

    const newMessage: Message = {
      id: messages.length + 1,
      role: "user",
      content: input,
      timestamp: new Date(),
    };

    setMessages([...messages, newMessage]);
    setInput("");
    
    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    // Simulate analysis for demo
    if (input.toLowerCase().includes("github.com") || input.toLowerCase().includes("repo") || input.toLowerCase().includes("analyze")) {
      setIsAnalyzing(true);
      toast.success("Analysis started!", {
        description: "Scanning repository for vulnerabilities...",
      });
      
      setTimeout(() => {
        const response: Message = {
          id: messages.length + 2,
          role: "assistant",
          content: "I've completed the analysis! Found 3 medium-severity vulnerabilities and 1 low-severity issue. The main concerns are outdated dependencies in the Express.js middleware layer. Would you like me to generate a detailed report?",
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, response]);
        setIsAnalyzing(false);
        toast.success("Analysis complete!", {
          description: "Found 4 vulnerabilities",
        });
      }, 3000);
    } else {
      // Handle general questions
      setTimeout(() => {
        const response: Message = {
          id: messages.length + 2,
          role: "assistant",
          content: "I can help you with CVE analysis and security scanning. Try pasting a GitHub repository URL or asking about specific vulnerabilities!",
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, response]);
      }, 500);
    }
  };

  const handleQuickAction = (action: string) => {
    setInput(action);
    textareaRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
      <ScrollArea ref={scrollAreaRef} className="flex-1">
        <div className="max-w-4xl mx-auto p-4 lg:p-6 space-y-6">
          {messages.length === 1 && (
            <div className="text-center py-8 lg:py-12 animate-fade-in">
              <div className="w-16 h-16 bg-gradient-to-br from-primary/10 to-accent/10 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-sm">
                <Sparkles className="w-8 h-8 text-primary" />
              </div>
              <h2 className="text-2xl lg:text-3xl font-bold text-foreground mb-2">
                Start Your Security Analysis
              </h2>
              <p className="text-muted-foreground max-w-md mx-auto text-sm lg:text-base">
                Paste a GitHub repository URL or ask me about CVE vulnerabilities in your codebase
              </p>

              <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4 max-w-3xl mx-auto">
                <button 
                  onClick={() => handleQuickAction("Analyze github.com/example/repo")}
                  className="p-4 bg-card border border-border rounded-xl hover:border-primary transition-all hover:shadow-sm text-left group"
                >
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center group-hover:bg-primary/20 transition-colors flex-shrink-0">
                      <GitBranch className="w-5 h-5 text-primary" />
                    </div>
                    <div className="min-w-0">
                      <div className="font-medium text-foreground mb-1">Analyze Repository</div>
                      <div className="text-sm text-muted-foreground">Scan a GitHub repo for vulnerabilities</div>
                    </div>
                  </div>
                </button>

                <button 
                  onClick={() => handleQuickAction("What are the most critical CVEs this month?")}
                  className="p-4 bg-card border border-border rounded-xl hover:border-primary transition-all hover:shadow-sm text-left group"
                >
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 bg-accent/10 rounded-lg flex items-center justify-center group-hover:bg-accent/20 transition-colors flex-shrink-0">
                      <Sparkles className="w-5 h-5 text-accent" />
                    </div>
                    <div className="min-w-0">
                      <div className="font-medium text-foreground mb-1">Ask About CVEs</div>
                      <div className="text-sm text-muted-foreground">Get info on specific vulnerabilities</div>
                    </div>
                  </div>
                </button>

                <button 
                  onClick={() => handleQuickAction("Generate a security report")}
                  className="p-4 bg-card border border-border rounded-xl hover:border-primary transition-all hover:shadow-sm text-left group"
                >
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 bg-success/10 rounded-lg flex items-center justify-center group-hover:bg-success/20 transition-colors flex-shrink-0">
                      <FileText className="w-5 h-5 text-success" />
                    </div>
                    <div className="min-w-0">
                      <div className="font-medium text-foreground mb-1">Generate Report</div>
                      <div className="text-sm text-muted-foreground">Create detailed security report</div>
                    </div>
                  </div>
                </button>
              </div>
            </div>
          )}

          {messages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))}

          {isAnalyzing && <AnalysisProgress />}
        </div>
      </ScrollArea>

      <div className="border-t border-border bg-card p-4 lg:p-6 flex-shrink-0">
        <div className="max-w-4xl mx-auto">
          <div className="flex gap-2 lg:gap-3">
            <Textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => {
                setInput(e.target.value);
                // Auto-resize textarea
                e.target.style.height = 'auto';
                e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
              }}
              onKeyDown={handleKeyDown}
              placeholder="Paste a GitHub URL or ask a question..."
              className="min-h-[52px] max-h-[120px] resize-none bg-secondary/50 border-border focus:border-primary transition-colors"
              disabled={isAnalyzing}
            />
            <Button
              onClick={handleSend}
              disabled={!input.trim() || isAnalyzing}
              className="bg-primary hover:bg-primary-hover text-primary-foreground h-[52px] px-4 lg:px-6 shadow-sm transition-all disabled:opacity-50 flex-shrink-0"
            >
              {isAnalyzing ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </Button>
          </div>
          <p className="text-xs text-muted-foreground mt-2 text-center">
            Press Enter to send, Shift + Enter for new line
          </p>
        </div>
      </div>
    </div>
  );
}
