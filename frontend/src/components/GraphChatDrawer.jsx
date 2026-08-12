import React, { useState } from 'react';
import { MessageSquare, X, Send, Bot, User, Sparkles } from 'lucide-react';
import { simulateGraphChat } from '../mockData';

export default function GraphChatDrawer({ isOpen, onClose, activeModel }) {
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: 'assistant',
      text: `Hello! I am your GraphRAG Companion powered by ${activeModel}. Ask me anything about your saved memories, or ask me to synthesize connections between concepts.`,
      entities: ['ChromaDB', 'Memory Engine'],
    },
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  const handleSend = (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMsg = { id: Date.now(), sender: 'user', text: input };
    setMessages((prev) => [...prev, userMsg]);
    const userQuery = input;
    setInput('');
    setIsTyping(true);

    setTimeout(() => {
      const chatRes = simulateGraphChat(userQuery);
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          sender: 'assistant',
          text: chatRes.reply,
          entities: chatRes.entities,
          latency: chatRes.latency_ms,
        },
      ]);
      setIsTyping(false);
    }, 1800);
  };

  if (!isOpen) return null;

  return (
    <div
      className="position-fixed top-0 end-0 bottom-0 bg-mono-surface border-start border-mono shadow-lg d-flex flex-column"
      style={{ width: '380px', maxWidth: '100vw', zIndex: 1050 }}
    >
      {/* Drawer Header */}
      <div className="p-3 border-bottom border-mono d-flex align-items-center justify-content-between bg-mono-dark">
        <div className="d-flex align-items-center gap-2">
          <Sparkles size={18} className="text-light" />
          <h5 className="h6 mb-0 text-white font-weight-bold">GraphRAG Companion</h5>
        </div>
        <button
          className="btn btn-mono-outline btn-sm p-1 text-secondary"
          onClick={onClose}
        >
          <X size={16} />
        </button>
      </div>

      {/* Messages List */}
      <div className="flex-grow-1 p-3 overflow-auto d-flex flex-column gap-3">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`d-flex flex-column ${
              msg.sender === 'user' ? 'align-items-end' : 'align-items-start'
            }`}
          >
            <div
              className={`p-3 rounded-3 max-w-85 font-mono fs-8 ${
                msg.sender === 'user'
                  ? 'bg-secondary text-dark fw-semibold'
                  : 'bg-mono-dark border border-mono-muted text-light'
              }`}
            >
              <div className="d-flex align-items-center gap-1 mb-1 opacity-75 fs-8">
                {msg.sender === 'user' ? <User size={12} /> : <Bot size={12} />}
                <span>{msg.sender === 'user' ? 'You' : 'GraphRAG AI'}</span>
              </div>
              <p className="mb-0 text-wrap whitespace-pre-wrap">{msg.text}</p>

              {msg.entities?.length > 0 && (
                <div className="mt-2 pt-2 border-top border-mono-muted d-flex flex-wrap gap-1">
                  {msg.entities.map((e) => (
                    <span key={e} className="badge bg-mono-dark text-secondary border border-mono fs-8">
                      {e}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {isTyping && (
          <div className="text-secondary font-mono fs-8 d-flex align-items-center gap-2 p-2 bg-mono-dark border border-mono-muted rounded">
            <span className="spinner-border spinner-border-sm text-light me-1" role="status" aria-hidden="true"></span>
            <span>Multi-hop entity lookup in progress...</span>
          </div>
        )}
      </div>

      {/* Input Form */}
      <form onSubmit={handleSend} className="p-3 border-top border-mono bg-mono-dark">
        <div className="input-group input-group-sm">
          <input
            type="text"
            className="form-control form-control-mono"
            placeholder="Ask GraphRAG companion..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
          />
          <button type="submit" className="btn btn-mono-primary btn-sm" disabled={!input.trim()}>
            <Send size={14} />
          </button>
        </div>
      </form>
    </div>
  );
}
