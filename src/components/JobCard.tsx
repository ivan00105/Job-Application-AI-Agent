/**
 * JobCard Component - Displays job with application tracking
 */
import { useState } from 'react';
import { MapPin, Building2, DollarSign, CheckCircle } from 'lucide-react';
import { applicationsAPI } from '../api/client';

interface Job {
    id: string;
    title: string;
    company: string | null;
    location: string | null;
    salary: string | null;
    description: string;
    url: string;
    posted_date: string | null;
    applied: boolean;
}

interface JobCardProps {
    job: Job;
    onApplicationUpdate?: () => void;
}

export const JobCard = ({ job, onApplicationUpdate }: JobCardProps) => {
    const [applied, setApplied] = useState(job.applied);
    const [loading, setLoading] = useState(false);

    const handleMarkApplied = async (e: React.MouseEvent) => {
        e.stopPropagation();
        setLoading(true);

        try {
            if (applied) {
                await applicationsAPI.remove(job.id);
                setApplied(false);
            } else {
                await applicationsAPI.markApplied(job.id);
                setApplied(true);
            }
            if (onApplicationUpdate) {
                onApplicationUpdate();
            }
        } catch (err) {
            console.error('Failed to update application status', err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
            <div className="flex justify-between items-start mb-3">
                <div>
                    <h3 className="text-xl font-semibold text-gray-900">{job.title}</h3>
                    {job.company && (
                        <div className="flex items-center gap-2 text-gray-600 mt-1">
                            <Building2 size={16} />
                            <span>{job.company}</span>
                        </div>
                    )}
                </div>
                {applied && (
                    <span className="flex items-center gap-1 px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
                        <CheckCircle size={16} />
                        Applied
                    </span>
                )}
            </div>

            <div className="flex gap-4 text-sm text-gray-600 mb-3">
                {job.location && (
                    <div className="flex items-center gap-1">
                        <MapPin size={14} />
                        <span>{job.location}</span>
                    </div>
                )}
                {job.salary && (
                    <div className="flex items-center gap-1">
                        <DollarSign size={14} />
                        <span>{job.salary}</span>
                    </div>
                )}
            </div>

            <p className="text-gray-700 mb-4 line-clamp-3">{job.description}</p>

            <div className="flex gap-3">
                <a
                    href={job.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                >
                    View Job
                </a>
                <button
                    onClick={handleMarkApplied}
                    disabled={loading}
                    className={`px-4 py-2 border rounded transition-colors ${applied
                            ? 'border-gray-300 text-gray-700 hover:bg-gray-50'
                            : 'border-green-600 text-green-600 hover:bg-green-50'
                        } disabled:opacity-50`}
                >
                    {loading ? 'Updating...' : applied ? 'Unmark Applied' : 'Mark as Applied'}
                </button>
            </div>

            {job.posted_date && (
                <p className="text-xs text-gray-500 mt-3">
                    Posted: {new Date(job.posted_date).toLocaleDateString()}
                </p>
            )}
        </div>
    );
};

