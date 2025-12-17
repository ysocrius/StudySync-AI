import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import AudioPlayer from './components/AudioPlayer';
import ChatInterface from './components/ChatInterface';
import VideoSummary from './components/VideoSummary';
import SourceManager from './components/SourceManager';
import { Sparkles, ArrowLeft } from 'lucide-react';

function App() {
    const [isSetupComplete, setIsSetupComplete] = useState(false);

    return (
        <div className="min-h-screen relative overflow-hidden bg-gray-50 text-gray-900 font-sans selection:bg-purple-200">
            {/* Background Mesh Gradient */}
            <div className="fixed inset-0 z-0 opacity-30 pointer-events-none"
                style={{ background: 'var(--bg-mesh)' }} />

            <div className="relative z-10 flex flex-col min-h-screen">
                {/* Glass Header */}
                <header className="sticky top-4 z-50 mx-4 md:mx-auto max-w-7xl">
                    <div className="glass-card rounded-2xl px-6 py-4 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            {isSetupComplete && (
                                <button onClick={() => setIsSetupComplete(false)} className="md:hidden mr-2 text-gray-400">
                                    <ArrowLeft size={20} />
                                </button>
                            )}
                            <div className="bg-gradient-to-tr from-purple-600 to-blue-500 p-2 rounded-xl text-white shadow-lg shadow-purple-500/20">
                                <Sparkles size={24} />
                            </div>
                            <div>
                                <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-gray-900 to-gray-600">
                                    Citrine & Sage Integration
                                </h1>
                                <p className="text-xs font-medium text-gray-500 tracking-wide uppercase">Interactive Study Companion</p>
                            </div>
                        </div>
                        <div className="hidden md:flex items-center gap-2 text-sm font-medium text-gray-500 bg-gray-100/50 px-3 py-1 rounded-full border border-gray-200/50">
                            <span className={`w-2 h-2 rounded-full ${isSetupComplete ? 'bg-green-500 animate-pulse' : 'bg-yellow-500'}`}></span>
                            {isSetupComplete ? 'AI Online' : 'Setup Mode'}
                        </div>
                    </div>
                </header>

                {/* Main Content */}
                <main className="flex-1 max-w-7xl mx-auto w-full px-4 py-8">
                    <AnimatePresence mode="wait">
                        {!isSetupComplete ? (
                            <motion.div
                                key="setup"
                                initial={{ opacity: 0, scale: 0.95 }}
                                animate={{ opacity: 1, scale: 1 }}
                                exit={{ opacity: 0, scale: 1.05 }}
                                transition={{ duration: 0.3 }}
                            >
                                <SourceManager onComplete={() => setIsSetupComplete(true)} />
                            </motion.div>
                        ) : (
                            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                                {/* Left Column: Summary & Audio */}
                                <div className="lg:col-span-7 space-y-8">
                                    <motion.div
                                        initial={{ opacity: 0, y: 20 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        transition={{ duration: 0.5 }}
                                    >
                                        <AudioPlayer />
                                    </motion.div>

                                    <motion.div
                                        initial={{ opacity: 0, y: 20 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        transition={{ duration: 0.5, delay: 0.1 }}
                                    >
                                        <VideoSummary />
                                    </motion.div>
                                </div>

                                {/* Right Column: Chat */}
                                <div className="lg:col-span-5 relative">
                                    <motion.div
                                        className="sticky top-28"
                                        initial={{ opacity: 0, x: 20 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        transition={{ duration: 0.5, delay: 0.2 }}
                                    >
                                        <ChatInterface />
                                    </motion.div>
                                </div>
                            </div>
                        )}
                    </AnimatePresence>
                </main>
            </div>
        </div>
    );
}

export default App;
