import { useState, useRef, useEffect } from "react";
import { Send, Sparkles, GitBranch, FileText, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ChatMessage } from "./ChatMessage";
import { AnalysisProgress } from "./AnalysisProgress";
import { toast } from "sonner";
import { Socket } from "socket.io-client";
import { 
  createAnalysis, 
  connectToAnalysis, 
  disconnectSocket, 
  extractGitHubUrl,
  getAnalysisResults,
  type Analysis,
  type AnalysisType,
  type ProgressUpdate,
  type AnalysisComplete,
} from "@/services/api";

type Message = {
  id: number;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  analysisId?: number;
};

type AnalysisState = {
  id: number;
  progress: number;
  stage: string;
  status: string;
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
  const [analysisState, setAnalysisState] = useState<AnalysisState | null>(null);
  const [currentSocket, setCurrentSocket] = useState<Socket | null>(null);
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

  // Cleanup socket on unmount
  useEffect(() => {
    return () => {
      if (currentSocket) {
        disconnectSocket(currentSocket);
      }
    };
  }, [currentSocket]);

  const handleSend = async () => {
    if (!input.trim() || isAnalyzing) return;

    const userMessage: Message = {
      id: Date.now(),
      role: "user",
      content: input,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    const userInput = input;
    setInput("");
    
    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    // Check if input contains a GitHub URL
    const githubUrl = extractGitHubUrl(userInput);
    
    if (githubUrl) {
      // Start real analysis
      await startAnalysis(githubUrl, userInput);
    } else {
      // Handle general questions
      setTimeout(() => {
        const response: Message = {
          id: Date.now(),
          role: "assistant",
          content: "I can help you analyze GitHub repositories for CVE vulnerabilities! Please paste a GitHub repository URL to get started. For example:\n\n`https://github.com/user/repository`\n\nI support three analysis types:\n- **SHORT** (2-3 min): Quick scan\n- **MEDIUM** (5-10 min): Standard audit with AI validation ⭐\n- **HARD** (15-40 min): Deep comprehensive scan",
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, response]);
      }, 500);
    }
  };

  const startAnalysis = async (repoUrl: string, userInput: string) => {
    setIsAnalyzing(true);

    // Determine analysis type from user input
    let analysisType: AnalysisType = 'SHORT'; // Default
    const inputLower = userInput.toLowerCase();
    if (inputLower.includes('quick') || inputLower.includes('short') || inputLower.includes('fast')) {
      analysisType = 'SHORT';
    } else if (inputLower.includes('deep') || inputLower.includes('hard') || inputLower.includes('comprehensive')) {
      analysisType = 'HARD';
    }

    try {
      // Create analysis
      const analysis = await createAnalysis(repoUrl, analysisType);
      
      const initialResponse: Message = {
        id: Date.now(),
        role: "assistant",
        content: `🚀 Analysis started for **${repoUrl}**\n\nAnalysis Type: **${analysisType}**\nAnalysis ID: ${analysis.analysis_id}\n\nConnecting to analysis agent...`,
        timestamp: new Date(),
        analysisId: analysis.analysis_id,
      };
      setMessages(prev => [...prev, initialResponse]);

      setAnalysisState({
        id: analysis.analysis_id,
        progress: 0,
        stage: 'pending',
        status: 'pending',
      });

      toast.success("Analysis started!", {
        description: `Scanning ${repoUrl}...`,
      });

      // Connect to WebSocket for real-time updates
      const socket = connectToAnalysis(analysis.analysis_id, {
        onConnect: () => {
          console.log('🔌 WebSocket Connected - Analysis ID:', analysis.analysis_id);
        },
        onAnalysisStarted: (data) => {
          const msg: Message = {
            id: Date.now(),
            role: "assistant",
            content: `✅ ${data.message}\n\nStarting automated security scan...`,
            timestamp: new Date(),
          };
          setMessages(prev => [...prev, msg]);
        },
        onProgress: (data: ProgressUpdate) => {
          console.log('🔄 Progress Update Received:', data);
          setAnalysisState({
            id: analysis.analysis_id,
            progress: data.progress,
            stage: data.stage,
            status: 'running',
          });
          console.log('✅ State updated:', { progress: data.progress, stage: data.stage });
        },
        onIntermediateResult: (data) => {
          const msg: Message = {
            id: Date.now(),
            role: "assistant",
            content: `🔍 Found vulnerability: **${data.cve_id}**\n- File: \`${data.file_path}\`\n- Severity: **${data.severity}**\n- Confidence: ${(data.confidence_score * 100).toFixed(1)}%`,
            timestamp: new Date(),
          };
          setMessages(prev => [...prev, msg]);
        },
        onComplete: async (data: AnalysisComplete) => {
          setIsAnalyzing(false);
          setAnalysisState(null);
          
          try {
            // Add small delay to ensure database is updated
            await new Promise(resolve => setTimeout(resolve, 500));
            
            // Retry logic for fetching results
            let results;
            let retries = 3;
            while (retries > 0) {
              try {
                results = await getAnalysisResults(analysis.analysis_id);
                break;
              } catch (error: any) {
                if (error.message.includes('not completed yet') && retries > 1) {
                  console.log(`Retrying... (${retries - 1} attempts left)`);
                  await new Promise(resolve => setTimeout(resolve, 1000));
                  retries--;
                } else {
                  throw error;
                }
              }
            }
            
            if (results) {
              const completionMsg: Message = {
                id: Date.now(),
                role: "assistant",
                content: `🎉 **Analysis Complete!**\n\n**Summary:**\n- Total Files: ${results.summary.total_files}\n- Code Chunks: ${results.summary.total_chunks}\n- Vulnerabilities Found: ${results.summary.total_findings}\n- Confirmed: ${results.summary.confirmed_vulnerabilities}\n- False Positives: ${results.summary.false_positives}\n\n**Severity Breakdown:**\n${Object.entries(results.summary.severity_breakdown).map(([severity, count]) => `- ${severity}: ${count}`).join('\n')}\n\n**Duration:** ${Math.round(data.duration_seconds)}s\n\nWould you like me to show detailed findings?`,
                timestamp: new Date(),
                analysisId: analysis.analysis_id,
              };
              setMessages(prev => [...prev, completionMsg]);

              toast.success("Analysis complete!", {
                description: `Found ${results.summary.total_findings} vulnerabilities`,
              });
            }
          } catch (error) {
            console.error('Error fetching results:', error);
            
            // Fallback message if we can't fetch results
            const fallbackMsg: Message = {
              id: Date.now(),
              role: "assistant",
              content: `🎉 **Analysis Complete!**\n\n**Summary:**\n- Duration: ${Math.round(data.duration_seconds)}s\n- Total Findings: ${data.total_findings}\n\nAnalysis ID: ${analysis.analysis_id}\n\nYou can view the full report in the Reports section.`,
              timestamp: new Date(),
              analysisId: analysis.analysis_id,
            };
            setMessages(prev => [...prev, fallbackMsg]);
            
            toast.success("Analysis complete!", {
              description: `Completed in ${Math.round(data.duration_seconds)}s`,
            });
          }

          // Disconnect socket
          if (currentSocket) {
            disconnectSocket(currentSocket);
            setCurrentSocket(null);
          }
        },
        onError: (data) => {
          setIsAnalyzing(false);
          setAnalysisState(null);
          
          const errorMsg: Message = {
            id: Date.now(),
            role: "assistant",
            content: `❌ **Analysis Error**\n\n${data.message}\n\n${data.details ? `Details: ${data.details}` : ''}${data.stage ? `\nStage: ${data.stage}` : ''}`,
            timestamp: new Date(),
          };
          setMessages(prev => [...prev, errorMsg]);

          toast.error("Analysis failed", {
            description: data.message,
          });

          if (currentSocket) {
            disconnectSocket(currentSocket);
            setCurrentSocket(null);
          }
        },
      });

      setCurrentSocket(socket);

    } catch (error: any) {
      setIsAnalyzing(false);
      setAnalysisState(null);
      
      const errorMsg: Message = {
        id: Date.now(),
        role: "assistant",
        content: `❌ Failed to start analysis: ${error.message}`,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMsg]);

      toast.error("Failed to start analysis", {
        description: error.message,
      });
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

          {isAnalyzing && analysisState && (
            <>
              {console.log('🎨 Rendering AnalysisProgress:', analysisState)}
              <AnalysisProgress 
                progress={analysisState.progress}
                stage={analysisState.stage}
                status={analysisState.status}
              />
            </>
          )}
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
