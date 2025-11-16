/**
 * JobCard Component - Displays job with application tracking
 */
import { useState, useEffect, useRef } from 'react';
import { MapPin, Building2, DollarSign, Bookmark, FileText, MessageSquare, Gift, CheckCircle, XCircle, Ban, RotateCcw, ThumbsDown, ChevronDown, Loader2, Sparkles, Target, FileText as FileTextIcon, Mail, Eye } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { applicationsAPI } from '../api/client';
import { interviewAPI } from '../api/interviewClient';

type ApplicationStatus =
    | 'saved'
    | 'applied'
    | 'interviewing'
    | 'offer'
    | 'accepted'
    | 'rejected'
    | 'declined'
    | 'withdrawn'
    | 'not_interested'
    | null;

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
    application_status?: ApplicationStatus;
    application_id?: string;
}

interface JobCardProps {
    job: Job;
    onApplicationUpdate?: () => void;
    onFindSimilar?: (jobId: string) => void;
    onPrepareInterview?: (jobId: string) => void;
    onPrepareCV?: (jobId: string) => void;
    onPrepareCoverLetter?: (jobId: string) => void;
    preparationStatus?: {
        has_tailored_cv: boolean;
        tailored_cv_id: string | null;
        has_cover_letter: boolean;
        cover_letter_id: string | null;
    };
}

const STATUS_CONFIG: Record<string, { label: string; icon: any; color: string; bgColor: string }> = {
    saved: { label: 'Saved', icon: Bookmark, color: 'text-blue-800', bgColor: 'bg-blue-100' },
    applied: { label: 'Applied', icon: FileText, color: 'text-yellow-800', bgColor: 'bg-yellow-100' },
    interviewing: { label: 'Interviewing', icon: MessageSquare, color: 'text-purple-800', bgColor: 'bg-purple-100' },
    offer: { label: 'Offer Received', icon: Gift, color: 'text-amber-800', bgColor: 'bg-amber-100' },
    accepted: { label: 'Accepted', icon: CheckCircle, color: 'text-green-800', bgColor: 'bg-green-100' },
    rejected: { label: 'Rejected', icon: XCircle, color: 'text-red-800', bgColor: 'bg-red-100' },
    declined: { label: 'Declined', icon: Ban, color: 'text-gray-800', bgColor: 'bg-gray-100' },
    withdrawn: { label: 'Withdrawn', icon: RotateCcw, color: 'text-gray-800', bgColor: 'bg-gray-100' },
    not_interested: { label: 'Not Interested', icon: ThumbsDown, color: 'text-gray-800', bgColor: 'bg-gray-100' },
};

export const JobCard = ({ job, onApplicationUpdate, onFindSimilar, onPrepareInterview, onPrepareCV, onPrepareCoverLetter, preparationStatus }: JobCardProps) => {
    const navigate = useNavigate();
    const [status, setStatus] = useState<ApplicationStatus>(job.application_status || null);
    const [loading, setLoading] = useState(false);
    const [findingSimilar, setFindingSimilar] = useState(false);
    const [isOpen, setIsOpen] = useState(false);
    const [isPrepareMenuOpen, setIsPrepareMenuOpen] = useState(false);
    const [interviewSessionsCount, setInterviewSessionsCount] = useState<number>(0);
    const [loadingSessions, setLoadingSessions] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);
    const prepareMenuRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        setStatus(job.application_status || null);
    }, [job.application_status]);

    // Load interview sessions count for saved/applied jobs
    useEffect(() => {
        if (job.applied || job.application_status === 'saved' || job.application_status === 'applied' || job.application_status === 'interviewing') {
            loadInterviewSessionsCount();
        }
    }, [job.id, job.applied, job.application_status]);

    const loadInterviewSessionsCount = async () => {
        try {
            setLoadingSessions(true);
            const data = await interviewAPI.getSessionsByJob(job.id);
            setInterviewSessionsCount(data.sessions?.length || 0);
        } catch (err) {
            console.error('Failed to load interview sessions count:', err);
            setInterviewSessionsCount(0);
        } finally {
            setLoadingSessions(false);
        }
    };

    // Close dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
            if (prepareMenuRef.current && !prepareMenuRef.current.contains(event.target as Node)) {
                setIsPrepareMenuOpen(false);
            }
        };

        if (isOpen || isPrepareMenuOpen) {
            document.addEventListener('mousedown', handleClickOutside);
        }

        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [isOpen, isPrepareMenuOpen]);

    const handleStatusChange = async (newStatus: ApplicationStatus) => {
        if (loading) return;

        setIsOpen(false);
        setLoading(true);
        try {
            if (newStatus === null) {
                // Remove application
                await applicationsAPI.remove(job.id);
                setStatus(null);
            } else if (status === null) {
                // Create new application with status
                await applicationsAPI.markApplied(job.id, newStatus);
                setStatus(newStatus);
            } else {
                // Update existing application status
                await applicationsAPI.updateStatus(job.id, newStatus);
                setStatus(newStatus);
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

    const handleFindSimilar = async () => {
        if (findingSimilar || !onFindSimilar) return;

        setFindingSimilar(true);
        try {
            await onFindSimilar(job.id);
        } catch (err) {
            console.error('Failed to find similar jobs', err);
        } finally {
            setFindingSimilar(false);
        }
    };

    const handlePrepareInterview = () => {
        setIsPrepareMenuOpen(false);
        if (onPrepareInterview) {
            onPrepareInterview(job.id);
        }
    };

    const handlePrepareCV = () => {
        setIsPrepareMenuOpen(false);
        if (onPrepareCV) {
            onPrepareCV(job.id);
        }
    };

    const handlePrepareCoverLetter = () => {
        setIsPrepareMenuOpen(false);
        if (onPrepareCoverLetter) {
            onPrepareCoverLetter(job.id);
        }
    };

    const statusOptions: Array<{ value: ApplicationStatus; label: string; icon: any; color: string; bgColor: string }> = [
        { value: null, label: 'No Status', icon: null, color: 'text-gray-600', bgColor: 'bg-gray-50' },
        { value: 'saved', label: 'Saved', icon: Bookmark, color: 'text-blue-700', bgColor: 'bg-blue-50' },
        { value: 'applied', label: 'Applied', icon: FileText, color: 'text-yellow-700', bgColor: 'bg-yellow-50' },
        { value: 'interviewing', label: 'Interviewing', icon: MessageSquare, color: 'text-purple-700', bgColor: 'bg-purple-50' },
        { value: 'offer', label: 'Offer Received', icon: Gift, color: 'text-amber-700', bgColor: 'bg-amber-50' },
        { value: 'accepted', label: 'Accepted', icon: CheckCircle, color: 'text-green-700', bgColor: 'bg-green-50' },
        { value: 'rejected', label: 'Rejected', icon: XCircle, color: 'text-red-700', bgColor: 'bg-red-50' },
        { value: 'declined', label: 'Declined', icon: Ban, color: 'text-gray-700', bgColor: 'bg-gray-50' },
        { value: 'withdrawn', label: 'Withdrawn', icon: RotateCcw, color: 'text-gray-700', bgColor: 'bg-gray-50' },
        { value: 'not_interested', label: 'Not Interested', icon: ThumbsDown, color: 'text-gray-700', bgColor: 'bg-gray-50' },
    ];

    const StatusIcon = status ? STATUS_CONFIG[status]?.icon : null;
    const statusConfig = status ? STATUS_CONFIG[status] : null;

    return (
        <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
            <div className="flex justify-between items-start mb-3">
                <div className="flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                        <h3 className="text-xl font-semibold text-gray-900">{job.title}</h3>
                        {/* Preparation indicators */}
                        {(job.applied || job.application_status === 'saved' || job.application_status === 'applied' || job.application_status === 'interviewing') && preparationStatus && (
                            <div className="flex items-center gap-1">
                                {preparationStatus.has_tailored_cv && preparationStatus.tailored_cv_id && (
                                    <button
                                        type="button"
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            navigate(`/applications/prepare/cv/${preparationStatus.tailored_cv_id}`);
                                        }}
                                        className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full text-xs font-medium hover:bg-blue-200 transition-colors cursor-pointer"
                                        title="Click to view Tailored CV"
                                    >
                                        <FileTextIcon size={12} />
                                        CV
                                    </button>
                                )}
                                {preparationStatus.has_cover_letter && preparationStatus.cover_letter_id && (
                                    <button
                                        type="button"
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            navigate(`/applications/prepare/cover-letter/${preparationStatus.cover_letter_id}`);
                                        }}
                                        className="inline-flex items-center gap-1 px-2 py-0.5 bg-green-100 text-green-700 rounded-full text-xs font-medium hover:bg-green-200 transition-colors cursor-pointer"
                                        title="Click to view Cover Letter"
                                    >
                                        <Mail size={12} />
                                        Letter
                                    </button>
                                )}
                            </div>
                        )}
                    </div>
                    {job.company && (
                        <div className="flex items-center gap-2 text-gray-600 mt-1">
                            <Building2 size={16} />
                            <span>{job.company}</span>
                        </div>
                    )}
                </div>
                {status && statusConfig && (
                    <span className={`flex items-center gap-1 px-3 py-1 ${statusConfig.bgColor} ${statusConfig.color} rounded-full text-sm font-medium whitespace-nowrap`}>
                        {StatusIcon && <StatusIcon size={16} />}
                        {statusConfig.label}
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

            {/* Interview Sessions Link */}
            {(job.applied || job.application_status === 'saved' || job.application_status === 'applied' || job.application_status === 'interviewing') && (
                <div className="mb-4 border-t border-gray-200 pt-3">
                    <button
                        type="button"
                        onClick={() => navigate(`/interviews?job_id=${job.id}`)}
                        className="flex items-center gap-2 text-sm text-purple-600 hover:text-purple-700 font-medium transition-colors"
                    >
                        <MessageSquare size={16} />
                        <span>View Mock Interviews</span>
                        {loadingSessions ? (
                            <Loader2 size={14} className="animate-spin" />
                        ) : interviewSessionsCount > 0 && (
                            <span className="bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full text-xs font-semibold">
                                {interviewSessionsCount}
                            </span>
                        )}
                    </button>
                </div>
            )}

            <div className="flex gap-3 flex-wrap">
                <a
                    href={job.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium shadow-sm"
                >
                    View Job
                </a>


                {onFindSimilar && (
                    <button
                        type="button"
                        onClick={handleFindSimilar}
                        disabled={findingSimilar}
                        className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium shadow-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                        {findingSimilar ? (
                            <>
                                <Loader2 className="h-4 w-4 animate-spin" />
                                Finding...
                            </>
                        ) : (
                            <>
                                <Sparkles className="h-4 w-4" />
                                Find Similar
                            </>
                        )}
                    </button>
                )}

                {/* Prepare Dropdown - Only show for saved/applied jobs */}
                {(job.applied || job.application_status === 'saved' || job.application_status === 'applied' || job.application_status === 'interviewing') && (
                    <div className="relative" ref={prepareMenuRef}>
                        <button
                            type="button"
                            onClick={() => setIsPrepareMenuOpen(!isPrepareMenuOpen)}
                            className="px-4 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg hover:from-purple-700 hover:to-indigo-700 transition-all font-medium shadow-sm flex items-center gap-2"
                        >
                            <Sparkles className="h-4 w-4" />
                            Prepare
                            <ChevronDown
                                size={16}
                                className={`transition-transform duration-200 ${isPrepareMenuOpen ? 'transform rotate-180' : ''}`}
                            />
                        </button>

                        {isPrepareMenuOpen && (
                            <div className="absolute z-50 mt-2 w-64 bg-white rounded-lg shadow-xl border border-gray-200 overflow-hidden dropdown-animation">
                                <div className="py-1">
                                    <button
                                        type="button"
                                        onClick={handlePrepareInterview}
                                        className="w-full flex items-center gap-3 px-4 py-3 text-left text-gray-700 hover:bg-purple-50 transition-colors"
                                    >
                                        <div className="bg-purple-100 p-2 rounded-lg">
                                            <Target className="h-5 w-5 text-purple-600" />
                                        </div>
                                        <div className="flex-1">
                                            <div className="font-medium">Interview Prep</div>
                                            <div className="text-xs text-gray-500">Practice with job-specific questions</div>
                                        </div>
                                    </button>

                                    {preparationStatus?.has_tailored_cv && preparationStatus?.tailored_cv_id ? (
                                        <button
                                            type="button"
                                            onClick={() => {
                                                setIsPrepareMenuOpen(false);
                                                navigate(`/applications/prepare/cv/${preparationStatus.tailored_cv_id}`);
                                            }}
                                            className="w-full flex items-center gap-3 px-4 py-3 text-left text-gray-700 hover:bg-blue-50 transition-colors border-t border-gray-100"
                                        >
                                            <div className="bg-blue-100 p-2 rounded-lg">
                                                <Eye className="h-5 w-5 text-blue-600" />
                                            </div>
                                            <div className="flex-1">
                                                <div className="font-medium">View Tailored CV</div>
                                                <div className="text-xs text-gray-500">View your saved CV for this job</div>
                                            </div>
                                        </button>
                                    ) : (
                                        <button
                                            type="button"
                                            onClick={handlePrepareCV}
                                            className="w-full flex items-center gap-3 px-4 py-3 text-left text-gray-700 hover:bg-blue-50 transition-colors border-t border-gray-100"
                                        >
                                            <div className="bg-blue-100 p-2 rounded-lg">
                                                <FileTextIcon className="h-5 w-5 text-blue-600" />
                                            </div>
                                            <div className="flex-1">
                                                <div className="font-medium">Tailored CV</div>
                                                <div className="text-xs text-gray-500">Customize your resume for this job</div>
                                            </div>
                                        </button>
                                    )}

                                    {preparationStatus?.has_cover_letter && preparationStatus?.cover_letter_id ? (
                                        <button
                                            type="button"
                                            onClick={() => {
                                                setIsPrepareMenuOpen(false);
                                                navigate(`/applications/prepare/cover-letter/${preparationStatus.cover_letter_id}`);
                                            }}
                                            className="w-full flex items-center gap-3 px-4 py-3 text-left text-gray-700 hover:bg-green-50 transition-colors border-t border-gray-100"
                                        >
                                            <div className="bg-green-100 p-2 rounded-lg">
                                                <Eye className="h-5 w-5 text-green-600" />
                                            </div>
                                            <div className="flex-1">
                                                <div className="font-medium">View Cover Letter</div>
                                                <div className="text-xs text-gray-500">View your saved cover letter</div>
                                            </div>
                                        </button>
                                    ) : (
                                        <button
                                            type="button"
                                            onClick={handlePrepareCoverLetter}
                                            className="w-full flex items-center gap-3 px-4 py-3 text-left text-gray-700 hover:bg-green-50 transition-colors border-t border-gray-100"
                                        >
                                            <div className="bg-green-100 p-2 rounded-lg">
                                                <Mail className="h-5 w-5 text-green-600" />
                                            </div>
                                            <div className="flex-1">
                                                <div className="font-medium">Cover Letter</div>
                                                <div className="text-xs text-gray-500">Generate a personalized cover letter</div>
                                            </div>
                                        </button>
                                    )}
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* Beautiful Status Selector */}
                <div className="relative" ref={dropdownRef}>
                    <button
                        type="button"
                        onClick={() => !loading && setIsOpen(!isOpen)}
                        disabled={loading}
                        className={`
                            flex items-center gap-2 px-4 py-2 rounded-lg border transition-all duration-200
                            font-medium shadow-sm min-w-[160px] justify-between
                            ${status && statusConfig
                                ? `${statusConfig.bgColor} ${statusConfig.color} border-transparent hover:shadow-md`
                                : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                            }
                            ${loading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                            ${isOpen ? 'ring-2 ring-blue-500 ring-offset-1' : ''}
                        `}
                    >
                        <div className="flex items-center gap-2">
                            {loading ? (
                                <>
                                    <Loader2 className="h-4 w-4 animate-spin" />
                                    <span className="text-sm">Updating...</span>
                                </>
                            ) : (
                                <>
                                    {status && StatusIcon ? (
                                        <>
                                            <StatusIcon size={16} />
                                            <span className="text-sm">{statusConfig?.label}</span>
                                        </>
                                    ) : (
                                        <span className="text-sm">Set Status</span>
                                    )}
                                </>
                            )}
                        </div>
                        {!loading && (
                            <ChevronDown
                                size={16}
                                className={`transition-transform duration-200 ${isOpen ? 'transform rotate-180' : ''}`}
                            />
                        )}
                    </button>

                    {/* Dropdown Menu */}
                    {isOpen && !loading && (
                        <div className="absolute z-50 mt-2 w-64 bg-white rounded-lg shadow-xl border border-gray-200 overflow-hidden dropdown-animation">
                            <div className="py-1 max-h-80 overflow-y-auto">
                                {statusOptions.map((option) => {
                                    const OptionIcon = option.icon;
                                    const isSelected = status === option.value;

                                    return (
                                        <button
                                            key={option.value || 'none'}
                                            type="button"
                                            onClick={() => handleStatusChange(option.value)}
                                            className={`
                                                w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors
                                                ${isSelected
                                                    ? `${option.bgColor} ${option.color} font-semibold`
                                                    : 'text-gray-700 hover:bg-gray-50'
                                                }
                                                ${option.value === null ? 'border-b border-gray-200' : ''}
                                            `}
                                        >
                                            {OptionIcon ? (
                                                <OptionIcon
                                                    size={18}
                                                    className={isSelected ? option.color : 'text-gray-400'}
                                                />
                                            ) : (
                                                <div className="w-[18px] h-[18px] rounded-full border-2 border-gray-300"></div>
                                            )}
                                            <span className="text-sm flex-1">{option.label}</span>
                                            {isSelected && (
                                                <CheckCircle size={16} className={option.color} />
                                            )}
                                        </button>
                                    );
                                })}
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {job.posted_date && (
                <p className="text-xs text-gray-500 mt-3">
                    Posted: {new Date(job.posted_date).toLocaleDateString()}
                </p>
            )}
        </div>
    );
};

