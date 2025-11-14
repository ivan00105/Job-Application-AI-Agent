import { useState, useEffect } from 'react';
import { Layout } from '../components/Layout';
import { applicationsAPI } from '../api/client';
import { Briefcase, Calendar, MapPin, ExternalLink, Trash2 } from 'lucide-react';

interface Application {
    id: string;
    job_id: string;
    applied_at: string;
    job: {
        id: string;
        title: string;
        company: string;
        location?: string;
        description?: string;
        job_url?: string;
        posted_date?: string;
    };
}

export const ApplicationsPage = () => {
    const [applications, setApplications] = useState<Application[]>([]);
    const [loading, setLoading] = useState(true);
    const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

    useEffect(() => {
        loadApplications();
    }, []);

    const loadApplications = async () => {
        try {
            setLoading(true);
            const data = await applicationsAPI.getApplications();
            setApplications(data.applications || []);
        } catch (err: any) {
            setMessage({
                type: 'error',
                text: err.response?.data?.detail || 'Failed to load applications',
            });
        } finally {
            setLoading(false);
        }
    };

    const handleRemove = async (jobId: string, applicationId: string) => {
        if (!confirm('Remove this application record?')) return;

        try {
            await applicationsAPI.remove(jobId);
            setApplications(applications.filter((app) => app.id !== applicationId));
            setMessage({ type: 'success', text: 'Application removed' });
            setTimeout(() => setMessage(null), 3000);
        } catch (err: any) {
            setMessage({
                type: 'error',
                text: err.response?.data?.detail || 'Failed to remove application',
            });
        }
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
        });
    };

    return (
        <Layout>
            <div className="max-w-6xl mx-auto p-6">
                <div className="mb-6">
                    <h1 className="text-3xl font-bold mb-2">My Applications</h1>
                    <p className="text-gray-600">Track all jobs you've applied to</p>
                </div>

                {message && (
                    <div
                        className={`mb-6 p-4 rounded ${message.type === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
                            }`}
                    >
                        {message.text}
                    </div>
                )}

                {loading ? (
                    <div className="text-center py-12">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                        <p className="mt-4 text-gray-600">Loading applications...</p>
                    </div>
                ) : applications.length === 0 ? (
                    <div className="text-center py-12 bg-white rounded-lg shadow">
                        <Briefcase className="w-16 h-16 mx-auto text-gray-400 mb-4" />
                        <h2 className="text-xl font-semibold text-gray-700 mb-2">No Applications Yet</h2>
                        <p className="text-gray-600 mb-4">Start applying to jobs from the Jobs page</p>
                        <a
                            href="/jobs"
                            className="inline-block px-6 py-3 bg-blue-600 text-white rounded hover:bg-blue-700"
                        >
                            Browse Jobs
                        </a>
                    </div>
                ) : (
                    <div className="space-y-4">
                        {applications.map((app) => (
                            <div key={app.id} className="bg-white rounded-lg shadow p-6 hover:shadow-md transition">
                                <div className="flex justify-between items-start mb-4">
                                    <div className="flex-1">
                                        <h2 className="text-xl font-semibold text-gray-800 mb-2">
                                            {app.job.title}
                                        </h2>
                                        <div className="flex flex-wrap gap-4 text-sm text-gray-600">
                                            <span className="flex items-center gap-1">
                                                <Briefcase size={16} />
                                                {app.job.company}
                                            </span>
                                            {app.job.location && (
                                                <span className="flex items-center gap-1">
                                                    <MapPin size={16} />
                                                    {app.job.location}
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                    <button
                                        onClick={() => handleRemove(app.job_id, app.id)}
                                        className="text-red-600 hover:text-red-800 p-2"
                                        title="Remove application"
                                    >
                                        <Trash2 size={20} />
                                    </button>
                                </div>

                                {app.job.description && (
                                    <p className="text-gray-700 mb-4 line-clamp-2">{app.job.description}</p>
                                )}

                                <div className="flex justify-between items-center pt-4 border-t">
                                    <div className="flex items-center gap-2 text-sm text-gray-500">
                                        <Calendar size={16} />
                                        <span>Applied: {formatDate(app.applied_at)}</span>
                                        {app.job.posted_date && (
                                            <span className="ml-4">Posted: {formatDate(app.job.posted_date)}</span>
                                        )}
                                    </div>
                                    {app.job.job_url && (
                                        <a
                                            href={app.job.job_url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="flex items-center gap-2 px-4 py-2 text-blue-600 hover:bg-blue-50 rounded"
                                        >
                                            View Job <ExternalLink size={16} />
                                        </a>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </Layout>
    );
};

