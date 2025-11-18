import { Loader2, CheckCircle2, AlertCircle, Sparkles, Brain, Target, FileText, CheckSquare, Wand2 } from 'lucide-react';

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

interface AgenticLoadingOverlayProps {
  isVisible: boolean;
  operation: 'generating' | 'regenerating' | 'refining';
  agentSteps?: AgentStep[];
  currentStep?: string;
  message?: string;
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

const operationLabels = {
  generating: 'Generating Your Tailored CV',
  regenerating: 'Regenerating Your Tailored CV',
  refining: 'Refining Your CV',
};

export const AgenticLoadingOverlay = ({
  isVisible,
  operation,
  agentSteps = [],
  currentStep,
  message
}: AgenticLoadingOverlayProps) => {
  if (!isVisible) return null;

  const getStepStatus = (step: AgentStep, index: number) => {
    if (step.success === false) return 'error';
    if (step.success === true) return 'completed';
    if (index === agentSteps.length - 1 && !currentStep) return 'active';
    return 'pending';
  };

  const getStepSummary = (step: AgentStep): string => {
    if (step.error) return `Error: ${step.error}`;
    
    const stepType = step.step || '';
    
    if (stepType.includes('analyze_job')) {
      const analysis = step.analysis || {};
      const skills = analysis.required_skills || [];
      if (skills.length > 0) {
        return `Identified ${skills.length} key requirements: ${skills.slice(0, 3).join(', ')}${skills.length > 3 ? '...' : ''}`;
      }
      return 'Extracted key requirements and qualifications';
    }
    
    if (stepType.includes('analyze_cv')) {
      const analysis = step.analysis || {};
      const experiences = analysis.relevant_experiences || [];
      const skills = analysis.relevant_skills || [];
      if (experiences.length > 0 || skills.length > 0) {
        return `Found ${experiences.length} relevant experiences and ${skills.length} matching skills`;
      }
      return 'Matched CV content to job requirements';
    }
    
    if (stepType.includes('create_strategy')) {
      const strategy = step.strategy || {};
      const approach = strategy.customization_approach || 'standard';
      return `Strategy: ${approach} approach with ${strategy.content_priorities?.length || 0} priorities`;
    }
    
    if (stepType.includes('generate_content')) {
      return 'Generated HTML CV with tailored content';
    }
    
    if (stepType.includes('validate_output')) {
      const validation = step.validation || {};
      const score = validation.quality_score || 0;
      const issues = validation.issues || [];
      if (issues.length > 0) {
        return `Quality score: ${score}/10. Found ${issues.length} issue${issues.length > 1 ? 's' : ''} to address`;
      }
      return `Quality score: ${score}/10. Validation passed`;
    }
    
    if (stepType.includes('refine_output')) {
      const round = step.refinement_round || 1;
      return `Refinement round ${round}: Improving CV quality and fixing issues`;
    }
    
    return 'Processing...';
  };

  // Expected steps for each operation
  const expectedSteps = operation === 'refining' 
    ? ['validate_output', 'refine_output']
    : ['analyze_job', 'analyze_cv', 'create_strategy', 'generate_content', 'validate_output', 'refine_output'];

  // Show all expected steps, marking completed ones
  // If we have agent steps, use them; otherwise show expected steps as pending
  const currentStepIndex = currentStep 
    ? expectedSteps.findIndex(key => currentStep?.includes(key))
    : -1;

  const allSteps = expectedSteps.map((stepKey, index) => {
    // Find the step in agent steps (check if step string contains the key)
    const completedStep = agentSteps.find(s => {
      const stepType = s.step || '';
      return stepType.includes(stepKey) || stepType === stepKey;
    });
    
    // Determine if this step is currently active
    const isActive = !completedStep && (
      (agentSteps.length === 0 && index === 0 && currentStepIndex === -1) ||
      (agentSteps.length > 0 && index === agentSteps.length) ||
      (currentStep && currentStep.includes(stepKey))
    );

    let simulatedStatus: 'completed' | 'active' | 'pending' | undefined;
    if (!completedStep && currentStepIndex >= 0) {
      if (index < currentStepIndex) simulatedStatus = 'completed';
      else if (index === currentStepIndex) simulatedStatus = 'active';
      else simulatedStatus = 'pending';
    }
    
    const status = completedStep 
      ? getStepStatus(completedStep, agentSteps.indexOf(completedStep)) 
      : simulatedStatus || (isActive ? 'active' : 'pending');
    
    return {
      key: stepKey,
      label: stepLabels[stepKey] || stepKey,
      icon: stepIcons[stepKey] || CheckSquare,
      status,
      summary: completedStep ? getStepSummary(completedStep) : undefined,
      step: completedStep
    };
  });

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6">
          <div className="flex items-center gap-3">
            <div className="relative">
              <Brain className="h-8 w-8 animate-pulse" />
              <div className="absolute inset-0 bg-white opacity-20 rounded-full animate-ping" />
            </div>
            <div>
              <h2 className="text-2xl font-bold">{operationLabels[operation]}</h2>
              <p className="text-blue-100 text-sm mt-1">AI Agent is working behind the scenes...</p>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {message && (
            <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-blue-800 text-sm">{message}</p>
            </div>
          )}

          <div className="space-y-4">
            {allSteps.length > 0 ? (
              allSteps.map((step, index) => {
                const Icon = step.icon;
                const isCompleted = step.status === 'completed';
                const isActive = step.status === 'active';
                const isError = step.status === 'error';
                const isPending = step.status === 'pending';

                return (
                  <div
                    key={step.key}
                    className={`flex items-start gap-4 p-4 rounded-lg border-2 transition-all ${
                      isActive
                        ? 'border-blue-500 bg-blue-50'
                        : isCompleted
                        ? 'border-green-500 bg-green-50'
                        : isError
                        ? 'border-red-500 bg-red-50'
                        : 'border-gray-200 bg-gray-50'
                    }`}
                  >
                    {/* Icon */}
                    <div className={`flex-shrink-0 ${isActive ? 'animate-pulse' : ''}`}>
                      {isCompleted ? (
                        <CheckCircle2 className="h-6 w-6 text-green-600" />
                      ) : isError ? (
                        <AlertCircle className="h-6 w-6 text-red-600" />
                      ) : isActive ? (
                        <Loader2 className="h-6 w-6 text-blue-600 animate-spin" />
                      ) : (
                        <Icon className="h-6 w-6 text-gray-400" />
                      )}
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <h3 className={`font-semibold ${
                        isActive ? 'text-blue-900' : isCompleted ? 'text-green-900' : isError ? 'text-red-900' : 'text-gray-600'
                      }`}>
                        {step.label}
                      </h3>
                      {step.summary && (
                        <p className={`text-sm mt-1 ${
                          isActive ? 'text-blue-700' : isCompleted ? 'text-green-700' : isError ? 'text-red-700' : 'text-gray-500'
                        }`}>
                          {step.summary}
                        </p>
                      )}
                      {isActive && (
                        <div className="mt-2">
                          <div className="h-1 bg-blue-200 rounded-full overflow-hidden">
                            <div className="h-full bg-blue-600 rounded-full animate-pulse" style={{ width: '60%' }} />
                          </div>
                        </div>
                      )}
                      {isPending && agentSteps.length === 0 && index === 0 && (
                        <p className="text-sm mt-1 text-gray-500 italic">
                          Waiting for AI agent to start...
                        </p>
                      )}
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="text-center py-8 text-gray-500">
                <Loader2 className="h-8 w-8 animate-spin mx-auto mb-2" />
                <p>Initializing AI agent...</p>
              </div>
            )}
          </div>

          {/* Additional refinement rounds info */}
          {operation === 'refining' && agentSteps.length > 0 && (
            <div className="mt-6 p-4 bg-purple-50 border border-purple-200 rounded-lg">
              <div className="flex items-center gap-2 text-purple-900 font-semibold">
                <Wand2 className="h-5 w-5" />
                <span>Refinement Progress</span>
              </div>
              <p className="text-purple-700 text-sm mt-2">
                The AI agent is iteratively improving your CV, validating quality, and fixing issues.
                This may take up to 5 refinement rounds to ensure optimal quality.
              </p>
            </div>
          )}

          {/* Summary of completed steps */}
          {agentSteps.length > 0 && (
            <div className="mt-6 p-4 bg-gray-50 border border-gray-200 rounded-lg">
              <div className="flex items-center gap-2 text-gray-900 font-semibold mb-2">
                <CheckSquare className="h-5 w-5" />
                <span>Agent Progress Summary</span>
              </div>
              <div className="text-sm text-gray-700">
                <p>Completed {agentSteps.filter(s => s.success !== false).length} of {allSteps.length} steps</p>
                {agentSteps.some(s => s.refinement_round) && (
                  <p className="mt-1">
                    Refinement rounds: {Math.max(...agentSteps.filter(s => s.refinement_round).map(s => s.refinement_round || 0), 0)}
                  </p>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 p-4 bg-gray-50">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4" />
              <span>Powered by AI Agent</span>
            </div>
            <div className="flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Please wait...</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

