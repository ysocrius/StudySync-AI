import { useState, useEffect } from 'react';
import api from '../api';
import { BookOpen } from 'lucide-react';

export default function VideoSummary() {
    const [summary, setSummary] = useState('');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchSummary = async () => {
            try {
                const res = await api.get('/api/summary');
                setSummary(res.data.summary);
            } catch (err) {
                console.error("Failed to load summary", err);
            } finally {
                setLoading(false);
            }
        };
        fetchSummary();
    }, []);

    return (
        <div className="bg-white p-6 rounded-lg shadow-md mb-6 border border-gray-200">
            <div className="flex items-center gap-2 mb-4 border-b pb-2">
                <BookOpen className="text-purple-600" />
                <h2 className="text-xl font-bold text-gray-800">Chapter & Video Summary</h2>
            </div>

            {loading ? (
                <div className="animate-pulse space-y-3">
                    <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                    <div className="h-4 bg-gray-200 rounded w-full"></div>
                    <div className="h-4 bg-gray-200 rounded w-5/6"></div>
                </div>
            ) : (
                <div className="prose prose-sm max-w-none text-gray-700 leading-relaxed whitespace-pre-line">
                    {summary || "No summary available."}
                </div>
            )}
        </div>
    );
}
