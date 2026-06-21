import React, { useState, useRef, useEffect } from 'react';
import { useProject } from '../../app/providers/ProjectProvider';
import { apiFetch } from '../../lib/api';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';

interface Source {
  filename: string;
  excerpt: string;
  score?: number;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];
}

export const ChatPage: React.FC = () => {
  const { activeProject } = useProject();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  if (!activeProject) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-8rem)] text-muted-foreground">
        <p>Select a project to start chatting.</p>
      </div>
    );
  }

  const handleSend = async () => {
    if (!input.trim()) return;
    
    const userMessage: Message = { role: 'user', content: input.trim() };
    const currentHistory = [...messages];
    
    setMessages([...currentHistory, userMessage]);
    setInput('');
    setIsTyping(true);

    try {
      const response = await apiFetch(`/v1/projects/${activeProject.project_id}/chat`, {
        method: 'POST',
        body: JSON.stringify({
          message: userMessage.content,
          history: currentHistory.map(m => ({ role: m.role, content: m.content }))
        })
      });
      
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response.answer,
        sources: response.sources
      }]);
    } catch (err: any) {
      console.error('Chat error', err);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: "Sorry, I encountered an error while processing your request. Please try again."
      }]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-6rem)] border rounded-xl overflow-hidden bg-background">
      {/* Header */}
      <div className="px-6 py-4 border-b bg-muted/30">
        <h2 className="font-semibold flex items-center gap-2">
          <svg className="w-5 h-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
          Research Assistant - {activeProject.name}
        </h2>
        <p className="text-xs text-muted-foreground mt-1">Ask questions across all documents in this project.</p>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center space-y-4 opacity-50">
            <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
              <svg className="w-8 h-8 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <div>
              <p className="text-lg font-medium">How can I help you today?</p>
              <p className="text-sm">Try asking about findings, contradictions, or summaries.</p>
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] rounded-2xl px-5 py-3 ${
              msg.role === 'user' 
                ? 'bg-primary text-primary-foreground rounded-tr-sm' 
                : 'bg-muted/50 border rounded-tl-sm'
            }`}>
              <div className={`prose prose-sm dark:prose-invert max-w-none prose-pre:bg-muted/80 prose-pre:text-foreground ${
                msg.role === 'user'
                  ? 'prose-p:text-primary-foreground prose-headings:text-primary-foreground prose-strong:text-primary-foreground prose-ul:text-primary-foreground prose-ol:text-primary-foreground prose-li:text-primary-foreground prose-a:text-primary-foreground prose-code:text-primary-foreground'
                  : 'prose-p:text-foreground prose-headings:text-foreground prose-strong:text-foreground prose-ul:text-foreground prose-ol:text-foreground prose-li:text-foreground prose-a:text-primary prose-code:text-foreground'
              }`}>
                <ReactMarkdown
                  remarkPlugins={[remarkMath]}
                  rehypePlugins={[rehypeKatex]}
                >
                  {msg.content}
                </ReactMarkdown>
              </div>
              
              {/* Source Citations */}
              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-4 pt-3 border-t border-border/50">
                  <p className="text-xs font-semibold mb-2 text-muted-foreground flex items-center gap-1">
                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    Sources
                  </p>
                  <div className="space-y-2">
                    {msg.sources.map((src, idx) => (
                      <div key={idx} className="bg-background rounded px-3 py-2 text-xs border shadow-sm">
                        <span className="font-medium text-primary block mb-1">{src.filename}</span>
                        <span className="text-muted-foreground italic line-clamp-2">"{src.excerpt}"</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}

        {isTyping && (
          <div className="flex justify-start">
            <div className="bg-muted/50 border rounded-2xl rounded-tl-sm px-5 py-4 flex space-x-1.5 items-center">
              <div className="w-2 h-2 rounded-full bg-foreground/40 animate-bounce" style={{ animationDelay: '0ms' }} />
              <div className="w-2 h-2 rounded-full bg-foreground/40 animate-bounce" style={{ animationDelay: '150ms' }} />
              <div className="w-2 h-2 rounded-full bg-foreground/40 animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 border-t bg-background">
        <div className="relative max-w-4xl mx-auto flex items-end gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question about your documents... (Press Enter to send)"
            className="w-full min-h-[60px] max-h-[200px] resize-none px-4 py-3 rounded-xl border bg-input text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 text-sm leading-relaxed"
            rows={1}
            disabled={isTyping}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isTyping}
            className="flex-shrink-0 w-12 h-[60px] flex items-center justify-center rounded-xl bg-primary text-primary-foreground hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 disabled:opacity-50 transition-all"
          >
            <svg className="w-5 h-5 translate-x-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 19V5m0 0l-7 7m7-7l7 7" />
            </svg>
          </button>
        </div>
        <div className="text-center mt-2">
          <span className="text-[10px] text-muted-foreground">AI can make mistakes. Verify important information from sources.</span>
        </div>
      </div>
    </div>
  );
};
