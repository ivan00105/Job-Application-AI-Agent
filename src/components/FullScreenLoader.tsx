/**
 * Full Screen Loader Component
 * A beautiful full-screen loading page for CV/Cover Letter generation
 */
import { Loader2, Sparkles, FileText, Mail, CheckCircle2, Target, Brain, CheckSquare, Wand2 } from 'lucide-react';

interface AgentStep {
  step?: string;
  success?: boolean;
  error?: string;
  analysis?: any;
  strategy?: any;
  validation?: any;
  refinement_round?: number;
  is_revalidation?: boolean;
}

interface FullScreenLoaderProps {
    type: 'cv' | 'cover-letter';
    message?: string;
    agentSteps?: AgentStep[];
    currentStep?: string;
}

const stepIcons: Record<string, any> = {
  'analyze_job': Target,
  'analyze_cv': FileText,
  'create_strategy': Brain,
  'generate_content': Sparkles,
  'validate_output': CheckSquare,
  'refine_output': Wand2,
};

const stepLabels: Record<string, string> = {
  'analyze_job': 'Analyzing Job Requirements',
  'analyze_cv': 'Analyzing Your CV',
  'create_strategy': 'Creating Tailoring Strategy',
  'generate_content': 'Generating CV Content',
  'validate_output': 'Validating Output',
  'refine_output': 'Refining CV',
};

const expectedSteps = ['analyze_job', 'analyze_cv', 'create_strategy', 'generate_content', 'validate_output', 'refine_output'];

export const FullScreenLoader = ({ type, message, agentSteps = [], currentStep }: FullScreenLoaderProps) => {
    const isCV = type === 'cv';
    const defaultMessage = isCV 
        ? 'Generating your tailored CV...' 
        : 'Generating your cover letter...';
    
    const displayMessage = message || defaultMessage;
    const Icon = isCV ? FileText : Mail;
    
    // Debug: Log agent steps for CV generation
    if (isCV && agentSteps.length > 0) {
        console.log('FullScreenLoader - Agent Steps:', agentSteps);
        console.log('FullScreenLoader - Current Step:', currentStep);
    }

    return (
        <div className="fixed inset-0 z-50 bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center">
            {/* Animated background elements */}
            <div className="absolute inset-0 overflow-hidden">
                <div className="absolute top-1/4 left-1/4 w-72 h-72 bg-blue-200 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob"></div>
                <div className="absolute top-1/3 right-1/4 w-72 h-72 bg-purple-200 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob" style={{ animationDelay: '2s' }}></div>
                <div className="absolute bottom-1/4 left-1/3 w-72 h-72 bg-indigo-200 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob" style={{ animationDelay: '4s' }}></div>
            </div>

            {/* Main content */}
            <div className="relative z-10 text-center px-4">
                <div className="mb-8 flex justify-center">
                    <div className="relative">
                        {/* Outer rotating ring */}
                        <div className="absolute inset-0 border-4 border-blue-200 rounded-full animate-spin-slow"></div>
                        
                        {/* Icon container */}
                        <div className={`relative w-24 h-24 rounded-full flex items-center justify-center ${
                            isCV ? 'bg-blue-100' : 'bg-green-100'
                        } shadow-lg`}>
                            <Icon className={`w-12 h-12 ${
                                isCV ? 'text-blue-600' : 'text-green-600'
                            }`} />
                            
                            {/* Sparkles animation */}
                            <div className="absolute inset-0 flex items-center justify-center">
                                <Sparkles className={`w-6 h-6 ${
                                    isCV ? 'text-blue-400' : 'text-green-400'
                                } animate-pulse`} />
                            </div>
                        </div>
                        
                        {/* Inner spinning loader */}
                        <div className="absolute inset-4 border-4 border-transparent border-t-blue-600 rounded-full animate-spin"></div>
                    </div>
                </div>

                <h2 className="text-3xl font-bold text-gray-800 mb-3">
                    {isCV ? 'Creating Your Tailored CV' : 'Writing Your Cover Letter'}
                </h2>
                
                <p className="text-lg text-gray-600 mb-6 max-w-md mx-auto">
                    {displayMessage}
                </p>

                {/* Agent Steps Progress - Always show for CV generation */}
                {isCV && (
                    <div className="mb-6 max-w-lg mx-auto">
                        <div className="bg-white/80 backdrop-blur-sm rounded-lg p-4 shadow-lg border border-blue-100">
                            <div className="space-y-2">
                                {expectedSteps.map((stepKey, index) => {
                                    // Find matching step - check both exact match and contains
                                    const completedStep = agentSteps.find(s => {
                                        if (!s || !s.step) return false;
                                        const stepType = String(s.step).toLowerCase();
                                        const stepKeyLower = stepKey.toLowerCase();
                                        return stepType === stepKeyLower || stepType.includes(stepKeyLower);
                                    });
                                    
                                    // Determine if this step is currently active
                                    // Active if: it's the first step and no steps completed, OR it's the next step after completed ones, OR currentStep matches
                                    const isActive = !completedStep && (
                                        (agentSteps.length === 0 && index === 0) ||
                                        (agentSteps.length > 0 && index === agentSteps.filter(s => s && s.success !== false).length) ||
                                        (currentStep && String(currentStep).toLowerCase().includes(stepKey.toLowerCase()))
                                    );
                                    
                                    const isCompleted = completedStep && completedStep.success !== false;
                                    const isError = completedStep && completedStep.success === false;
                                    
                                    const Icon = stepIcons[stepKey] || CheckSquare;
                                    const label = stepLabels[stepKey] || stepKey;
                                    
                                    return (
                                        <div
                                            key={stepKey}
                                            className={`flex items-center gap-3 p-2 rounded-md transition-all ${
                                                isActive
                                                    ? 'bg-blue-50 border border-blue-200'
                                                    : isCompleted
                                                    ? 'bg-green-50 border border-green-200'
                                                    : isError
                                                    ? 'bg-red-50 border border-red-200'
                                                    : 'bg-gray-50 border border-gray-200 opacity-60'
                                            }`}
                                        >
                                            <div className="flex-shrink-0">
                                                {isCompleted ? (
                                                    <CheckCircle2 className="h-5 w-5 text-green-600" />
                                                ) : isError ? (
                                                    <Loader2 className="h-5 w-5 text-red-600" />
                                                ) : isActive ? (
                                                    <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />
                                                ) : (
                                                    <Icon className="h-5 w-5 text-gray-400" />
                                                )}
                                            </div>
                                            <span className={`text-sm font-medium flex-1 ${
                                                isActive
                                                    ? 'text-blue-900'
                                                    : isCompleted
                                                    ? 'text-green-900'
                                                    : isError
                                                    ? 'text-red-900'
                                                    : 'text-gray-600'
                                            }`}>
                                                {label}
                                            </span>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    </div>
                )}

                {/* Progress dots - Show only for cover letters */}
                {!isCV && (
                    <div className="flex justify-center gap-2 mb-6">
                        <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                        <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                    </div>
                )}

                <p className="text-sm text-gray-500 mt-4">
                    {isCV 
                        ? agentSteps.length > 0 
                            ? `Step ${agentSteps.filter(s => s.success !== false).length} of ${expectedSteps.length} completed`
                            : `Starting step 1 of ${expectedSteps.length}...`
                        : 'This may take a few moments...'}
                </p>
            </div>

            {/* Add custom animations */}
            <style>{`
                @keyframes blob {
                    0%, 100% {
                        transform: translate(0, 0) scale(1);
                    }
                    33% {
                        transform: translate(30px, -50px) scale(1.1);
                    }
                    66% {
                        transform: translate(-20px, 20px) scale(0.9);
                    }
                }
                .animate-blob {
                    animation: blob 7s infinite;
                }
                .animate-spin-slow {
                    animation: spin 3s linear infinite;
                }
            `}</style>
        </div>
    );
};

