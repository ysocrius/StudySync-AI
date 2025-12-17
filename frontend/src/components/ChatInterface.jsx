import { useState } from 'react';
import { Send, User, Bot } from 'lucide-react';
import axios from 'axios';

export default function ChatInterface() {
    const [query, setQuery] = useState('');
    const [messages, setMessages] = useState([
        { role: 'assistant', text: 'Hello! I am your AI study companion. Ask me anything about the chapter or videos.' }
    ]);
    const [loading, setLoading] = useState(false);

    const handleSend = async (e) => {
        e.preventDefault();
        if (!query.trim()) return;

        try {
            setLoading(true);
            const userMsg = { role: 'user', text: query };
            const botMsgPlaceholder = { role: 'assistant', text: "Thinking...", sources: [] };

            setMessages(prev => [...prev, userMsg, botMsgPlaceholder]);
            setQuery("");

            // Using fetch for streaming support, but with dynamic URL
            const startUrl = (import.meta.env.VITE_API_URL || 'http://localhost:5000').replace(/\/$/, '');
            const response = await fetch(`${startUrl}/api/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: query })
            });

            if (!response.ok) throw new Error(response.statusText);

            // Start reading the stream
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let botText = "";
            let sources = [];

            // Update the placeholder to empty string to start filling
            setMessages(prev => {
                const newMsgs = [...prev];
                newMsgs[newMsgs.length - 1].text = "";
                return newMsgs;
            });

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                // Check for sources separator
                if (chunk.includes("__SOURCES__:")) {
                    const parts = chunk.split("__SOURCES__:");
                    botText += parts[0];
                    try {
                        sources = JSON.parse(parts[1]);
                    } catch (e) {
                        console.error("Failed to parse sources", e);
                    }
                } else {
                    botText += chunk;
                }

                setMessages(prev => {
                    const newMsgs = [...prev];
                    const lastMsg = newMsgs[newMsgs.length - 1];
                    lastMsg.text = botText;
                    lastMsg.sources = sources.length > 0 ? sources : lastMsg.sources;
                    return [...newMsgs];
                });
            }

        } catch (err) {
            console.error(err);
            setMessages(prev => {
                const newMsgs = [...prev];
                const lastMsg = newMsgs[newMsgs.length - 1];
                lastMsg.text = "Error: " + (err.message || "Failed to get response");
                lastMsg.isError = true;
                return [...newMsgs];
            });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-[500px] bg-white rounded-lg shadow-md border border-gray-200">
            {/* Header */}
            <div className="p-4 border-b border-gray-100 bg-white/50 backdrop-blur-sm flex items-center gap-2 sticky top-0 z-10">
                <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                <h2 className="font-semibold text-gray-700">AI Study Assistant</h2>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((msg, i) => (
                    <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[80%] rounded-lg p-3 ${msg.role === 'user' ? 'bg-blue-600 text-white' :
                            msg.isError ? 'bg-red-50 text-red-600 border border-red-200' : 'bg-gray-100 text-gray-800'
                            }`}>
                            <p className="text-sm whitespace-pre-wrap">{msg.text}</p>
                            {msg.sources && msg.sources.length > 0 && (
                                <div className="mt-3 pt-2 border-t border-gray-200/50">
                                    <p className="text-xs font-semibold text-gray-500 mb-1">Sources:</p>
                                    <div className="flex flex-wrap gap-1">
                                        {[...new Map(msg.sources.map(src => {
                                            const rawSource = src.metadata.source;
                                            let label = rawSource.split('/').pop().split('?')[0];
                                            let icon = '📄';

                                            // Format YouTube
                                            if (rawSource.includes('youtube') || rawSource.includes('youtu.be') || rawSource.includes('watch')) {
                                                icon = '📺';
                                                // Extract ID crudely
                                                const vidId = rawSource.includes('v=') ? rawSource.split('v=')[1].slice(0, 4) : rawSource.split('/').pop().slice(0, 4);
                                                label = `YouTube (${vidId}...)`;
                                            } else if (label.endsWith('.pdf')) {
                                                icon = '📚';
                                                label = label.length > 15 ? label.slice(0, 12) + '...' : label;
                                            }
                                            return [label, { label, icon, content: src.content }];
                                        })).values()].map((uniqueSrc, idx) => (
                                            <span key={idx} className="bg-white/50 border border-gray-300 px-1.5 py-0.5 rounded text-[10px] text-gray-600 truncate max-w-[150px]" title={uniqueSrc.content}>
                                                {uniqueSrc.icon} {uniqueSrc.label}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                ))}
                {loading && (
                    <div className="flex justify-start">
                        <div className="bg-gray-100 p-3 rounded-lg animate-pulse w-24 h-8"></div>
                    </div>
                )}
            </div>

            <form onSubmit={handleSend} className="p-3 border-t flex gap-2">
                <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Ask a question..."
                    className="flex-1 border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                    type="submit"
                    disabled={loading}
                    className="bg-blue-600 text-white p-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
                >
                    <Send size={18} />
                </button>
            </form>
        </div>
    );
}
