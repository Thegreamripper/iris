import React, { useEffect, useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface Message {
    type: 'transcription' | 'response' | 'wake_word_detected';
    message: string;
    timestamp: number;
}

const AdvancedAIFeatures: React.FC = () => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [isConnected, setIsConnected] = useState(false);
    const [isListening, setIsListening] = useState(false);
    const [currentEmotion, setCurrentEmotion] = useState<string>('');
    const wsRef = useRef<WebSocket | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        // Connect to WebSocket
        wsRef.current = new WebSocket('ws://localhost:8000/ws');

        wsRef.current.onopen = () => {
            console.log('Connected to WebSocket');
            setIsConnected(true);
        };

        wsRef.current.onclose = () => {
            console.log('Disconnected from WebSocket');
            setIsConnected(false);
        };

        wsRef.current.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type) {
                setMessages(prev => [...prev, {
                    ...data,
                    timestamp: Date.now()
                }]);

                // Update emotion if present
                if (data.emotion) {
                    setCurrentEmotion(data.emotion);
                }
            }
        };

        return () => {
            wsRef.current?.close();
        };
    }, []);

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const getMessageColor = (type: string) => {
        switch (type) {
            case 'wake_word_detected':
                return 'bg-purple-500/20';
            case 'transcription':
                return 'bg-blue-500/20';
            case 'response':
                return 'bg-green-500/20';
            default:
                return 'bg-gray-500/20';
        }
    };

    const renderMessage = (message: Message) => {
        const backgroundColor = getMessageColor(message.type);
        return (
            <motion.div
                key={message.timestamp}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className={`p-4 rounded-lg ${backgroundColor} backdrop-blur-lg mb-4`}
            >
                <div className="text-sm text-white/60 mb-1">
                    {message.type === 'wake_word_detected' && '🎤 Wake Word Detected'}
                    {message.type === 'transcription' && '👂 You said'}
                    {message.type === 'response' && '🤖 IRIS responds'}
                </div>
                <div className="text-white">{message.message}</div>
            </motion.div>
        );
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-purple-900 to-blue-900 text-white p-6">
            <div className="max-w-4xl mx-auto">
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-center mb-8"
                >
                    <h1 className="text-4xl font-bold mb-2">IRIS</h1>
                    <p className="text-xl text-white/80">Advanced AI Assistant</p>
                </motion.div>

                <div className="bg-white/10 rounded-lg p-6 backdrop-blur-lg mb-6">
                    <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center space-x-4">
                            <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                            <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
                        </div>
                        {currentEmotion && (
                            <div className="px-4 py-2 bg-white/5 rounded-full">
                                Detected Emotion: {currentEmotion}
                            </div>
                        )}
                    </div>

                    <div className="h-[600px] overflow-y-auto mb-4 space-y-4">
                        <AnimatePresence>
                            {messages.map(message => renderMessage(message))}
                        </AnimatePresence>
                        <div ref={messagesEndRef} />
                    </div>
                </div>

                <div className="text-center text-white/60">
                    <p>Just say "IRIS" to activate me!</p>
                    <p className="mt-2 text-sm">I'm always listening for your command.</p>
                </div>
            </div>
        </div>
    );
};

export default AdvancedAIFeatures; 