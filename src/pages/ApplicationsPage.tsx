import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Layout } from '../components/Layout';
import { AgenticLoadingOverlay } from '../components/AgenticLoadingOverlay';
import { applicationsAPI } from '../api/client';
import { 
    Briefcase, Bookmark, FileText, MessageSquare, Gift, 
    CheckCircle, XCircle, Ban 
} from 'lucide-react';
import { JobCard } from '../components/JobCard';
import { FullScreenLoader } from '../components/FullScreenLoader';

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

interface Application {
    id: string;
    job_id: string;
    status: string;
    notes?: string;
    applied_at: string;
    created_at: string;
    updated_at: string;
    job: {
        id: string;
        title: string;
        company: string;
        location?: string;
        description?: string;
        job_url?: string;
        posted_date?: string;
        salary?: string;
    };
}

const STATUS_TABS: Array<{ value: ApplicationStatus | 'all'; label: string; icon: any; count?: number }> = [
    { value: 'all', label: 'All', icon: Briefcase },
    { value: 'saved', label: 'Saved', icon: Bookmark },
    { value: 'applied', label: 'Applied', icon: FileText },
    { value: 'interviewing', label: 'Interviewing', icon: MessageSquare },
    { value: 'offer', label: 'Offer', icon: Gift },
    { value: 'accepted', label: 'Accepted', icon: CheckCircle },
    { value: 'rejected', label: 'Rejected', icon: XCircle },
    { value: 'declined', label: 'Declined', icon: Ban },
];


export const ApplicationsPage = () => {
    const navigate = useNavigate();
    const [searchParams, setSearchParams] = useSearchParams();
    const [applications, setApplications] = useState<Application[]>([]);
    const [loading, setLoading] = useState(true);
    
    // Initialize activeTab from URL parameter or default to 'all'
    const tabParam = searchParams.get('tab') as ApplicationStatus | 'all' | null;
    const [activeTab, setActiveTab] = useState<ApplicationStatus | 'all'>(
        tabParam && ['all', 'saved', 'applied', 'interviewing', 'offer', 'accepted', 'rejected', 'declined', 'withdrawn', 'not_interested'].includes(tabParam) 
            ? tabParam 
            : 'all'
    );
    const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
    const [preparationStatuses, setPreparationStatuses] = useState<Record<string, any>>({});
    const [generatingType, setGeneratingType] = useState<'cv' | 'cover-letter' | null>(null);
    const [agentSteps, setAgentSteps] = useState<any[]>([]);
    const [currentStep, setCurrentStep] = useState<string | undefined>();

    useEffect(() => {
        loadApplications();
    }, []);

    // Update URL when tab changes
    useEffect(() => {
        if (activeTab !== 'all') {
            setSearchParams({ tab: activeTab as string });
        } else {
            setSearchParams({});
        }
    }, [activeTab, setSearchParams]);

    const loadApplications = async () => {
        try {
            setLoading(true);
            const data = await applicationsAPI.getApplications();
            const apps = data.applications || [];
            setApplications(apps);
            
            // Load preparation statuses for all jobs
            const statusPromises = apps.map(async (app: Application) => {
                try {
                    const status = await applicationsAPI.getPreparationStatus(app.job_id);
                    return { jobId: app.job_id, status };
                } catch (err) {
                    return { jobId: app.job_id, status: null };
                }
            });
            
            const statuses = await Promise.all(statusPromises);
            const statusMap: Record<string, any> = {};
            statuses.forEach(({ jobId, status }) => {
                if (status) {
                    statusMap[jobId] = status;
                }
            });
            setPreparationStatuses(statusMap);
        } catch (err: any) {
            setMessage({
                type: 'error',
                text: err.response?.data?.detail || 'Failed to load applications',
            });
        } finally {
            setLoading(false);
        }
    };

    const handleApplicationUpdate = () => {
        loadApplications();
    };

    const handlePrepareInterview = async (jobId: string) => {
        try {
            const result = await applicationsAPI.prepareInterview(jobId);
            if (result.redirect_url) {
                navigate(result.redirect_url);
            }
        } catch (err: any) {
            setMessage({
                type: 'error',
                text: err.response?.data?.detail || 'Failed to start interview prep. Please try again.'
            });
        }
    };

    const handlePrepareCV = async (jobId: string) => {
        try {
            setGeneratingType('cv');
            setMessage(null); // Clear any previous messages
            setAgentSteps([]);
            setCurrentStep('generating');
            
            // Use streaming endpoint for real-time step updates
            await applicationsAPI.prepareCVStream(
                jobId,
                // onStepUpdate - called when a step starts or completes
                (update: any) => {
                    console.log('Step update received:', update);
                    
                    if (update.type === 'step_start') {
                        // Step is starting
                        setCurrentStep(update.step);
                    } else if (update.type === 'step_complete' && update.step_data) {
                        // Step completed - add to agent steps
                        setAgentSteps(prev => {
                            // Check if step already exists (for refinement rounds)
                            const existingIndex = prev.findIndex(
                                s => s.step === update.step_data.step && 
                                s.refinement_round === update.step_data.refinement_round
                            );
                            
                            if (existingIndex >= 0) {
                                // Update existing step
                                const newSteps = [...prev];
                                newSteps[existingIndex] = update.step_data;
                                return newSteps;
                            } else {
                                // Add new step
                                return [...prev, update.step_data];
                            }
                        });
                        
                        // Update current step to next expected step
                        const expectedSteps = ['analyze_job', 'analyze_cv', 'create_strategy', 'generate_content', 'validate_output', 'refine_output'];
                        const currentStepIndex = expectedSteps.indexOf(update.step_data.step);
                        if (currentStepIndex >= 0 && currentStepIndex < expectedSteps.length - 1) {
                            setCurrentStep(expectedSteps[currentStepIndex + 1]);
                        }
                    }
                },
                // onComplete - called when generation is complete
                (result: any) => {
                    console.log('CV Generation Complete:', result);
                    
                    // Set final agent steps
                    if (result.agent_steps) {
                        setAgentSteps(result.agent_steps);
                    }
                    
                    // Check if generation was successful
                    if (result.success && result.redirect_url) {
                        // Keep loader visible during navigation - overlay will show on TailoredCVPage
                        setTimeout(() => {
                            navigate(result.redirect_url);
                        }, 1000); // Small delay to show final steps
                    } else {
                        setGeneratingType(null);
                        setCurrentStep(undefined);
                        setMessage({
                            type: 'error',
                            text: result.error || 'CV generation completed but no redirect URL was provided.'
                        });
                    }
                },
                // onError - called on error
                (error: string) => {
                    console.error('CV Generation Error:', error);
                    setGeneratingType(null);
                    setCurrentStep(undefined);
                    
                    // Provide more helpful error messages
                    let errorMessage = error;
                    if (error.includes('CV profile not found') || error.includes('upload your CV')) {
                        errorMessage = 'Please upload your CV in the Profile page first before generating a tailored CV.';
                    } else if (error.includes('CV data')) {
                        errorMessage = 'Your CV data needs to be updated. Please re-upload your CV in the Profile page.';
                    } else if (error.includes('timeout') || error.includes('temporarily unavailable')) {
                        errorMessage = 'CV generation service is temporarily busy. Please try again in a moment.';
                    }
                    
                    setMessage({
                        type: 'error',
                        text: errorMessage
                    });
                    
                    // Auto-dismiss error after 8 seconds
                    setTimeout(() => setMessage(null), 8000);
                }
            );
        } catch (err: any) {
            setGeneratingType(null);
            setCurrentStep(undefined);
            const errorDetail = err.response?.data?.detail || err.message || 'Failed to generate tailored CV.';
            
            setMessage({
                type: 'error',
                text: errorDetail
            });
            
            // Auto-dismiss error after 8 seconds
            setTimeout(() => setMessage(null), 8000);
        }
    };

    const handlePrepareCoverLetter = async (jobId: string) => {
        try {
            setGeneratingType('cover-letter');
            setMessage(null); // Clear any previous messages
            const result = await applicationsAPI.prepareCoverLetter(jobId);
            if (result.redirect_url) {
                // Keep loader visible during navigation
                navigate(result.redirect_url);
            } else {
                setGeneratingType(null);
            }
        } catch (err: any) {
            setGeneratingType(null);
            setMessage({
                type: 'error',
                text: err.response?.data?.detail || 'Failed to generate cover letter. Please make sure you have uploaded your CV in the Profile page.'
            });
        }
    };

    // Filter applications by active tab
    const filteredApplications = activeTab === 'all' 
        ? applications 
        : applications.filter(app => app.status === activeTab);

    // Count applications by status
    const getStatusCount = (status: ApplicationStatus | 'all') => {
        if (status === 'all') return applications.length;
        return applications.filter(app => app.status === status).length;
    };

    // Convert application to job format for JobCard
    const applicationToJob = (app: Application) => {
        return {
            id: app.job.id,
            title: app.job.title,
            company: app.job.company,
            location: app.job.location || null,
            salary: app.job.salary || null,
            description: app.job.description || '',
            url: app.job.job_url || '',
            posted_date: app.job.posted_date || null,
            applied: true,
            application_status: app.status as ApplicationStatus,
            application_id: app.id,
        };
    };

    return (
        <>
            {generatingType && (
                <FullScreenLoader 
                    type={generatingType} 
                    agentSteps={agentSteps}
                    currentStep={currentStep}
                />
            )}
            <Layout>
                <div className="space-y-6">
                {/* Header */}
                <div>
                    <h1 className="text-3xl font-bold text-gray-900">Saved Jobs</h1>
                    <p className="text-gray-600 mt-1">Manage and track all your job applications</p>
                </div>

                {/* Status Tabs */}
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-1">
                    <div className="flex gap-1 overflow-x-auto">
                        {STATUS_TABS.map((tab) => {
                            const TabIcon = tab.icon;
                            const count = getStatusCount(tab.value);
                            const isActive = activeTab === tab.value;
                            
                            return (
                                <button
                                    key={tab.value}
                                    onClick={() => setActiveTab(tab.value)}
                                    className={`
                                        flex items-center gap-2 px-4 py-2.5 rounded-md text-sm font-medium
                                        transition-all duration-200 whitespace-nowrap
                                        ${isActive
                                            ? 'bg-blue-600 text-white shadow-sm'
                                            : 'text-gray-700 hover:bg-gray-100'
                                        }
                                    `}
                                >
                                    <TabIcon size={16} />
                                    <span>{tab.label}</span>
                                    {count > 0 && (
                                        <span className={`
                                            px-2 py-0.5 rounded-full text-xs font-semibold
                                            ${isActive
                                                ? 'bg-blue-500 text-white'
                                                : 'bg-gray-200 text-gray-700'
                                            }
                                        `}>
                                            {count}
                                        </span>
                                    )}
                                </button>
                            );
                        })}
                    </div>
                </div>

                {/* Message Alert */}
                {message && (
                    <div
                        className={`p-4 rounded-lg border ${
                            message.type === 'success' 
                                ? 'bg-green-50 border-green-200 text-green-800' 
                                : 'bg-red-50 border-red-200 text-red-800'
                        }`}
                    >
                        {message.text}
                    </div>
                )}

                {/* Content */}
                {loading ? (
                    <div className="text-center py-12 bg-white rounded-lg shadow-sm">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                        <p className="mt-4 text-gray-600">Loading saved jobs...</p>
                    </div>
                ) : filteredApplications.length === 0 ? (
                    <div className="text-center py-16 bg-white rounded-lg shadow-sm">
                        {activeTab === 'all' ? (
                            <>
                                <Bookmark className="w-16 h-16 mx-auto text-gray-400 mb-4" />
                                <h2 className="text-xl font-semibold text-gray-700 mb-2">No Saved Jobs Yet</h2>
                                <p className="text-gray-600 mb-6">Start saving jobs from the Jobs page to track your applications</p>
                                <a
                                    href="/jobs"
                                    className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium shadow-sm"
                                >
                                    <Briefcase size={18} />
                                    Browse Jobs
                                </a>
                            </>
                        ) : (
                            <>
                                {STATUS_TABS.find(t => t.value === activeTab)?.icon && (
                                    <div className="flex justify-center mb-4">
                                        {(() => {
                                            const TabIcon = STATUS_TABS.find(t => t.value === activeTab)!.icon;
                                            return <TabIcon className="w-16 h-16 text-gray-400" />;
                                        })()}
                                    </div>
                                )}
                                <h2 className="text-xl font-semibold text-gray-700 mb-2">
                                    No {STATUS_TABS.find(t => t.value === activeTab)?.label} Jobs
                                </h2>
                                <p className="text-gray-600">
                                    You don't have any jobs with this status yet.
                                </p>
                            </>
                        )}
                    </div>
                ) : (
                    <div className="grid gap-4">
                        {filteredApplications.map((app) => (
                            <JobCard
                                key={app.id}
                                job={applicationToJob(app)}
                                onApplicationUpdate={handleApplicationUpdate}
                                onPrepareInterview={handlePrepareInterview}
                                onPrepareCV={handlePrepareCV}
                                onPrepareCoverLetter={handlePrepareCoverLetter}
                                preparationStatus={preparationStatuses[app.job_id]}
                            />
                        ))}
                    </div>
                )}
            </div>
        </Layout>
        </>
    );
};

