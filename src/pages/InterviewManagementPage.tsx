/**
 * Interview Management Page
 * Combined page to start new interviews and manage all interview sessions
 */
import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Layout } from '../components/Layout';
import { interviewAPI } from '../api/interviewClient';
import { jobsAPI } from '../api/client';
import type { InterviewSession } from '../api/interviewClient';
import { 
    MessageSquare, PlayCircle, CheckCircle, Clock, BarChart3, 
    Loader2, Filter, X, ExternalLink
} from 'lucide-react';

export const InterviewManagementPage = () => {
    const navigate = useNavigate();
    const [searchParams, setSearchParams] = useSearchParams();
    const jobIdFilter = searchParams.get('job_id');
    
    const [sessions, setSessions] = useState<InterviewSession[]>([]);
    const [loading, setLoading] = useState(true);
    const [filterStatus, setFilterStatus] = useState<'all' | 'active' | 'completed' | 'abandoned'>('all');
    const [filterJobId, setFilterJobId] = useState<string | null>(jobIdFilter);
    const [jobTitles, setJobTitles] = useState<Record<string, string>>({});
    const [jobCompanies, setJobCompanies] = useState<Record<string, string>>({});
    const [filteredJobInfo, setFilteredJobInfo] = useState<{ title: string; company: string } | null>(null);

    useEffect(() => {
        loadSessions();
    }, [filterJobId]);

    useEffect(() => {
        if (jobIdFilter) {
            setFilterJobId(jobIdFilter);
        }
    }, [jobIdFilter]);

    const loadSessions = async () => {
        try {
            setLoading(true);
            let data;
            if (filterJobId) {
                data = await interviewAPI.getSessionsByJob(filterJobId);
                // Load job details for the filtered job
                try {
                    const job = await jobsAPI.getById(filterJobId);
                    setFilteredJobInfo({
                        title: job.title || 'Unknown Job',
                        company: job.company || 'Unknown Company'
                    });
                } catch (err) {
                    console.error(`Failed to load filtered job ${filterJobId}:`, err);
                    setFilteredJobInfo({
                        title: 'Unknown Job',
                        company: 'Unknown Company'
                    });
                }
            } else {
                data = await interviewAPI.getSessionHistory(100);
                setFilteredJobInfo(null);
            }
            const sessionsList = data.sessions || [];
            setSessions(sessionsList);
            
            // Load job titles for sessions with job_id
            const uniqueJobIds = [...new Set(sessionsList
                .filter(s => s.job_id)
                .map(s => s.job_id!)
            )];
            
            if (uniqueJobIds.length > 0) {
                const jobTitlePromises = uniqueJobIds.map(async (jobId) => {
                    try {
                        const job = await jobsAPI.getById(jobId);
                        return { 
                            jobId, 
                            title: job.title || 'Unknown Job',
                            company: job.company || 'Unknown Company'
                        };
                    } catch (err) {
                        console.error(`Failed to load job ${jobId}:`, err);
                        return { 
                            jobId, 
                            title: 'Unknown Job',
                            company: 'Unknown Company'
                        };
                    }
                });
                
                const jobTitlesData = await Promise.all(jobTitlePromises);
                const titlesMap: Record<string, string> = {};
                const companiesMap: Record<string, string> = {};
                jobTitlesData.forEach(({ jobId, title, company }) => {
                    titlesMap[jobId] = title;
                    companiesMap[jobId] = company;
                });
                setJobTitles(titlesMap);
                setJobCompanies(companiesMap);
            }
        } catch (err) {
            console.error('Failed to load interview sessions:', err);
            setSessions([]);
        } finally {
            setLoading(false);
        }
    };

    const clearJobFilter = () => {
        setFilterJobId(null);
        setFilteredJobInfo(null);
        setSearchParams({});
    };

    const filteredSessions = sessions.filter(session => {
        if (filterStatus === 'all') return true;
        return session.status === filterStatus;
    });

    const formatDate = (dateString: string | undefined) => {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', { 
            year: 'numeric', 
            month: 'short', 
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    return (
        <Layout>
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <div className="mb-8">
                    <div className="flex items-center justify-between mb-6">
                        <div>
                            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                                <MessageSquare className="text-purple-600" size={32} />
                                Interviews
                            </h1>
                            <p className="text-gray-600 mt-2">
                                View and manage all your mock interview sessions
                            </p>
                        </div>
                    </div>

                    {/* Filters */}
                    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
                        <div className="flex items-center gap-4 flex-wrap">
                            <div className="flex items-center gap-2">
                                <Filter size={18} className="text-gray-500" />
                                <span className="text-sm font-medium text-gray-700">Filters:</span>
                            </div>
                            
                            <div className="flex items-center gap-2">
                                <label className="text-sm text-gray-600">Status:</label>
                                <select
                                    value={filterStatus}
                                    onChange={(e) => setFilterStatus(e.target.value as any)}
                                    className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                                >
                                    <option value="all">All</option>
                                    <option value="active">Active</option>
                                    <option value="completed">Completed</option>
                                    <option value="abandoned">Abandoned</option>
                                </select>
                            </div>

                            {filterJobId && (
                                <div className="flex items-center gap-2 bg-purple-50 px-3 py-1.5 rounded-lg">
                                    <span className="text-sm text-purple-700">
                                        {filteredJobInfo 
                                            ? `${filteredJobInfo.title} (${filteredJobInfo.company})`
                                            : `Job ID: ${filterJobId.substring(0, 8)}...`}
                                    </span>
                                    <button
                                        type="button"
                                        onClick={clearJobFilter}
                                        className="text-purple-600 hover:text-purple-800"
                                    >
                                        <X size={16} />
                                    </button>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Sessions List */}
                {loading ? (
                    <div className="flex items-center justify-center py-12">
                        <Loader2 size={32} className="animate-spin text-purple-600" />
                    </div>
                ) : filteredSessions.length === 0 ? (
                    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
                        <MessageSquare size={48} className="mx-auto text-gray-400 mb-4" />
                        <h3 className="text-lg font-semibold text-gray-900 mb-2">No interview sessions found</h3>
                        <p className="text-gray-600 mb-6">
                            {filterJobId 
                                ? "No interview sessions found for this job. Start one from the job card's Prepare menu."
                                : "You haven't started any interview sessions yet. Start practicing from a saved job!"}
                        </p>
                        {filterJobId && (
                            <button
                                type="button"
                                onClick={clearJobFilter}
                                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                            >
                                View All Sessions
                            </button>
                        )}
                    </div>
                ) : (
                    <div className="space-y-4">
                        {filteredSessions.map((session) => {
                            const isActive = session.status === 'active';
                            const isCompleted = session.status === 'completed';
                            
                            return (
                                <div key={session.id} className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                                    {/* Session Header */}
                                    <div className="p-4">
                                        <div className="flex items-start justify-between">
                                            <div className="flex items-start gap-4 flex-1">
                                                <div className="mt-1">
                                                    {isActive ? (
                                                        <PlayCircle size={24} className="text-blue-600" />
                                                    ) : isCompleted ? (
                                                        <CheckCircle size={24} className="text-green-600" />
                                                    ) : (
                                                        <Clock size={24} className="text-gray-400" />
                                                    )}
                                                </div>
                                                
                                                <div className="flex-1 min-w-0">
                                                    {session.job_id && jobTitles[session.job_id] && (
                                                        <div className="mb-2">
                                                            <div className="text-sm font-semibold text-gray-900">
                                                                {jobTitles[session.job_id]}
                                                                {jobCompanies[session.job_id] && (
                                                                    <span className="text-gray-600 font-normal"> ({jobCompanies[session.job_id]})</span>
                                                                )}
                                                            </div>
                                                            <div className="text-xs text-gray-500">
                                                                {session.domain} Interview
                                                            </div>
                                                        </div>
                                                    )}
                                                    {!session.job_id && (
                                                        <div className="mb-2">
                                                            <div className="text-sm font-semibold text-gray-900">
                                                                {session.domain} Interview
                                                            </div>
                                                            <div className="text-xs text-gray-500">
                                                                General Practice Session
                                                            </div>
                                                        </div>
                                                    )}
                                                    <div className="flex items-center gap-3 mb-2">
                                                        <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                                                            isActive ? 'bg-blue-100 text-blue-700' :
                                                            isCompleted ? 'bg-green-100 text-green-700' :
                                                            'bg-gray-100 text-gray-700'
                                                        }`}>
                                                            {isActive ? 'In Progress' : isCompleted ? 'Completed' : 'Abandoned'}
                                                        </span>
                                                        {session.job_id && (
                                                            <button
                                                                type="button"
                                                                onClick={() => navigate(`/applications?tab=saved`)}
                                                                className="text-xs text-purple-600 hover:text-purple-700 flex items-center gap-1"
                                                            >
                                                                <ExternalLink size={12} />
                                                                View Job
                                                            </button>
                                                        )}
                                                    </div>
                                                    
                                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                                                        <div>
                                                            <div className="text-gray-500 text-xs mb-1">Progress</div>
                                                            <div className="font-semibold text-gray-900">
                                                                {session.completed_questions}/{session.total_questions} questions
                                                            </div>
                                                        </div>
                                                        {isCompleted && session.avg_score && (
                                                            <div>
                                                                <div className="text-gray-500 text-xs mb-1">Average Score</div>
                                                                <div className="font-semibold text-gray-900">
                                                                    {session.avg_score.toFixed(1)}/5.0
                                                                </div>
                                                            </div>
                                                        )}
                                                        <div>
                                                            <div className="text-gray-500 text-xs mb-1">Started</div>
                                                            <div className="font-semibold text-gray-900 text-xs">
                                                                {formatDate(session.started_at)}
                                                            </div>
                                                        </div>
                                                        {session.completed_at && (
                                                            <div>
                                                                <div className="text-gray-500 text-xs mb-1">Completed</div>
                                                                <div className="font-semibold text-gray-900 text-xs">
                                                                    {formatDate(session.completed_at)}
                                                                </div>
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>
                                            
                                            <div className="flex items-center gap-2 ml-4">
                                                {isActive && (
                                                    <button
                                                        type="button"
                                                        onClick={() => navigate(`/interview/session/${session.id}`)}
                                                        className="px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-700 transition-colors flex items-center gap-2"
                                                    >
                                                        <PlayCircle size={16} />
                                                        Continue
                                                    </button>
                                                )}
                                                {isCompleted && (
                                                    <button
                                                        type="button"
                                                        onClick={() => navigate(`/interview/session/${session.id}/results`)}
                                                        className="px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-700 transition-colors flex items-center gap-2"
                                                    >
                                                        <BarChart3 size={16} />
                                                        Results
                                                    </button>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>
        </Layout>
    );
};

