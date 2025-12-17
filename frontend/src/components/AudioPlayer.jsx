import { useState, useEffect, useRef } from 'react';
import { Play, Pause, FastForward } from 'lucide-react';
import api from '../api';

export default function AudioPlayer() {
    const [isPlaying, setIsPlaying] = useState(false);
    const [currentLineIndex, setCurrentLineIndex] = useState(0);
    const [dialogue, setDialogue] = useState([]);
    const [loading, setLoading] = useState(true);
    const audioRef = useRef(new Audio());

    useEffect(() => {
        const fetchDialogue = async () => {
            try {
                const res = await api.get('/api/dialogue');
                if (res.data.dialogue) {
                    setDialogue(res.data.dialogue);
                }
            } catch (err) {
                console.error("Failed to load dialogue", err);
            } finally {
                setLoading(false);
            }
        };
        fetchDialogue();
    }, []);

    useEffect(() => {
        const audio = audioRef.current;

        const handleEnded = () => {
            if (currentLineIndex < dialogue.length - 1) {
                setCurrentLineIndex(prev => prev + 1);
                // Auto play next
                setTimeout(() => playLine(currentLineIndex + 1), 500);
            } else {
                setIsPlaying(false);
            }
        };

        audio.addEventListener('ended', handleEnded);
        return () => audio.removeEventListener('ended', handleEnded);
    }, [currentLineIndex, dialogue]);

    const playLine = (index) => {
        if (index >= dialogue.length) return;
        const line = dialogue[index];
        if (audioRef.current.src !== line.audioUrl) { // Check if already set (naive check)
            // MVP: Assuming audioUrl is relative /static/audio/...
            audioRef.current.src = line.audioUrl;
        }
        audioRef.current.play();
        setIsPlaying(true);
        setCurrentLineIndex(index);
    };

    const togglePlay = () => {
        if (isPlaying) {
            audioRef.current.pause();
            setIsPlaying(false);
        } else {
            // Use current index or 0
            playLine(currentLineIndex);
        }
    };

    if (loading) return <div>Loading Podcast...</div>;

    return (
        <div className="bg-white p-4 rounded-lg shadow-md mb-6 border border-gray-200">
            <div className="flex items-center justify-between mb-2">
                <h2 className="text-lg font-semibold flex items-center gap-2">
                    🎧 Teacher-Student Podcast
                </h2>
                <button onClick={togglePlay} className="p-2 bg-black text-white rounded-full hover:bg-gray-800 transition">
                    {isPlaying ? <Pause size={20} /> : <Play size={20} />}
                </button>
            </div>

            {/* Transcript View */}
            <div className="h-48 overflow-y-auto bg-gray-50 p-2 rounded border text-sm space-y-2">
                {dialogue.map((line, idx) => (
                    <div
                        key={idx}
                        className={`p-2 rounded cursor-pointer transition ${idx === currentLineIndex ? 'bg-blue-100 border-l-4 border-blue-500' : 'hover:bg-gray-100'}`}
                        onClick={() => playLine(idx)}
                    >
                        <span className="font-bold text-xs uppercase tracking-wider text-gray-500">{line.speaker}</span>
                        <p className="text-gray-800">{line.text}</p>
                    </div>
                ))}
            </div>
        </div>
    );
}
