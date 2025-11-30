import { useState, useEffect } from 'react';
import { Layout } from '../components/Layout';
import { useParams, useNavigate } from 'react-router-dom';
import { gamesAPI, Game, GameSession, GameAttempt } from '../api/gamesClient';
import { CodeEditor } from '../components/CodeEditor';
import { ArrowLeft, CheckCircle, XCircle, Clock, Trophy, AlertCircle, ChevronLeft, ChevronRight } from 'lucide-react';

interface Question {
  description: string;
  function_signature?: string;
  starter_code: string;
  test_cases: Array<{
    name: string;
    input: any;
    expected_output: any;
  }>;
  concept?: string;
  question_number?: number;
}

export const CodingChallengePage = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [game, setGame] = useState<Game | null>(null);
  const [session, setSession] = useState<GameSession | null>(null);
  
  // Multi-question support
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [questionCodes, setQuestionCodes] = useState<Record<number, string>>({});
  const [questionAttempts, setQuestionAttempts] = useState<Record<number, GameAttempt | null>>({});
  const [questionProgress, setQuestionProgress] = useState<Record<number, { passed: boolean; score: number }>>({});
  
  const [timeElapsed, setTimeElapsed] = useState(0);
  const [error, setError] = useState<string | null>(null);

  // Check if game has multiple questions
  const isMultiQuestion = game?.game_content?.questions && Array.isArray(game.game_content.questions);
  const questions: Question[] = isMultiQuestion 
    ? game.game_content.questions 
    : game?.game_content 
      ? [{
          description: game.game_content.description || game.description || '',
          function_signature: game.game_content.function_signature,
          starter_code: game.game_content.starter_code || '',
          test_cases: game.game_content.test_cases || []
        }]
      : [];
  
  const currentQuestion = questions[currentQuestionIndex];
  const currentCode = questionCodes[currentQuestionIndex] || currentQuestion?.starter_code || '';
  const currentAttempt = questionAttempts[currentQuestionIndex] || null;

  useEffect(() => {
    if (sessionId) {
      loadSession();
    }
  }, [sessionId]);

  useEffect(() => {
    // Initialize code for all questions
    if (game && questions.length > 0) {
      const initialCodes: Record<number, string> = {};
      questions.forEach((q, idx) => {
        if (!questionCodes[idx]) {
          initialCodes[idx] = q.starter_code || '';
        }
      });
      if (Object.keys(initialCodes).length > 0) {
        setQuestionCodes(prev => ({ ...prev, ...initialCodes }));
      }
    }
  }, [game, questions]);

  useEffect(() => {
    if (session?.started_at && session.status === 'active') {
      const interval = setInterval(() => {
        const start = new Date(session.started_at!).getTime();
        const now = Date.now();
        setTimeElapsed(Math.floor((now - start) / 1000));
      }, 1000);
      return () => clearInterval(interval);
    }
  }, [session]);

  const loadSession = async () => {
    if (!sessionId) return;
    
    setLoading(true);
    try {
      const { session: sessionData, game: gameData } = await gamesAPI.getSession(sessionId);
      setSession(sessionData);
      setGame(gameData);
    } catch (err) {
      console.error('Failed to load session:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!sessionId || !currentCode.trim() || !currentQuestion) return;

    setSubmitting(true);
    setError(null);
    try {
      const answerData: any = {
        code: currentCode,
        language: game?.game_content?.language || 'python',
      };
      
      // Add question_index for multi-question games
      if (isMultiQuestion) {
        answerData.question_index = currentQuestionIndex;
      }
      
      const attempt = await gamesAPI.submitAnswer(sessionId, {
        session_id: sessionId,
        answer_data: answerData,
      });

      setQuestionAttempts(prev => ({
        ...prev,
        [currentQuestionIndex]: attempt
      }));

      // Update progress
      const evalResult = attempt.evaluation_result;
      if (evalResult) {
        setQuestionProgress(prev => ({
          ...prev,
          [currentQuestionIndex]: {
            passed: evalResult.passed || false,
            score: evalResult.passed_tests || 0
          }
        }));
      }
    } catch (err: any) {
      console.error('Failed to submit:', err);
      setError(err?.response?.data?.detail || 'Failed to submit code. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleCodeChange = (newCode: string) => {
    setQuestionCodes(prev => ({
      ...prev,
      [currentQuestionIndex]: newCode
    }));
  };

  const handleReset = () => {
    if (currentQuestion?.starter_code) {
      setQuestionCodes(prev => ({
        ...prev,
        [currentQuestionIndex]: currentQuestion.starter_code
      }));
    }
    setQuestionAttempts(prev => ({
      ...prev,
      [currentQuestionIndex]: null
    }));
  };

  const handleQuestionChange = (newIndex: number) => {
    if (newIndex >= 0 && newIndex < questions.length) {
      setCurrentQuestionIndex(newIndex);
      setError(null);
    }
  };

  const handleComplete = async () => {
    if (!sessionId) return;

    // Check if all questions are answered (for multi-question games)
    if (isMultiQuestion) {
      const allAnswered = questions.every((_, idx) => {
        const progress = questionProgress[idx];
        return progress && progress.passed;
      });
      
      if (!allAnswered) {
        setError('Please complete all questions before finishing the challenge.');
        return;
      }
    } else {
      // Single question - check if passed
      const evalResult = currentAttempt?.evaluation_result;
      if (!evalResult?.passed) {
        setError('Please pass all test cases before completing the challenge.');
        return;
      }
    }

    setSubmitting(true);
    setError(null);
    try {
      const result = await gamesAPI.completeSession(sessionId);
      navigate(`/games/results/${sessionId}`, { state: { result } });
    } catch (err: any) {
      console.error('Failed to complete:', err);
      const errorMessage = err?.response?.data?.detail || err?.message || 'Failed to complete challenge. Please try again.';
      setError(errorMessage);
    } finally {
      setSubmitting(false);
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getQuestionStatus = (index: number) => {
    const progress = questionProgress[index];
    if (progress?.passed) return 'completed';
    if (progress) return 'attempted';
    return 'not-started';
  };

  const allQuestionsCompleted = isMultiQuestion 
    ? questions.every((_, idx) => questionProgress[idx]?.passed)
    : currentAttempt?.evaluation_result?.passed;

  if (loading) {
    return (
      <Layout>
        <div className="max-w-6xl mx-auto">
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
            <p className="mt-4 text-gray-600">Loading challenge...</p>
          </div>
        </div>
      </Layout>
    );
  }

  if (!game || !session || !currentQuestion) {
    return (
      <Layout>
        <div className="max-w-6xl mx-auto">
          <div className="bg-white border rounded-xl p-8 text-center">
            <AlertCircle className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Challenge not found</h2>
            <button
              onClick={() => navigate('/games')}
              className="mt-6 px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition font-medium"
            >
              Return to Challenge Center
            </button>
          </div>
        </div>
      </Layout>
    );
  }

  const evaluationResult = currentAttempt?.evaluation_result;
  const testResults = evaluationResult?.test_results || [];
  const allPassed = evaluationResult?.passed || false;

  return (
    <Layout>
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <button
            onClick={() => navigate('/games')}
            className="flex items-center text-gray-600 hover:text-gray-900"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Challenge Center
          </button>
          <div className="flex items-center gap-4">
            {isMultiQuestion && (
              <div className="text-sm text-gray-600">
                Question {currentQuestionIndex + 1} of {questions.length}
              </div>
            )}
            {session.started_at && (
              <div className="flex items-center gap-2 text-gray-600">
                <Clock className="h-4 w-4" />
                <span className="text-sm font-medium">{formatTime(timeElapsed)}</span>
              </div>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Question Navigation (for multi-question games) */}
          {isMultiQuestion && questions.length > 1 && (
            <div className="lg:col-span-1">
              <div className="bg-white border rounded-xl p-4 sticky top-4">
                <h3 className="text-sm font-semibold text-gray-900 mb-3">Questions</h3>
                <div className="space-y-2">
                  {questions.map((q, idx) => {
                    const status = getQuestionStatus(idx);
                    return (
                      <button
                        key={idx}
                        onClick={() => handleQuestionChange(idx)}
                        className={`w-full text-left p-3 rounded-lg border transition ${
                          currentQuestionIndex === idx
                            ? 'bg-purple-50 border-purple-300'
                            : status === 'completed'
                            ? 'bg-green-50 border-green-200 hover:bg-green-100'
                            : status === 'attempted'
                            ? 'bg-yellow-50 border-yellow-200 hover:bg-yellow-100'
                            : 'bg-gray-50 border-gray-200 hover:bg-gray-100'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-medium text-gray-900">
                              Question {idx + 1}
                            </span>
                            {q.concept && (
                              <span className="text-xs text-gray-500">({q.concept})</span>
                            )}
                          </div>
                          {status === 'completed' && (
                            <CheckCircle className="h-4 w-4 text-green-600" />
                          )}
                        </div>
                      </button>
                    );
                  })}
                </div>
                <div className="mt-4 pt-4 border-t">
                  <div className="text-xs text-gray-600">
                    <div>Completed: {Object.values(questionProgress).filter(p => p?.passed).length} / {questions.length}</div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Main Content */}
          <div className={`space-y-4 ${isMultiQuestion && questions.length > 1 ? 'lg:col-span-2' : 'lg:col-span-2'}`}>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Problem Description */}
              <div className="space-y-4">
                <div className="bg-white border rounded-xl p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h1 className="text-xl font-bold text-gray-900">
                      {isMultiQuestion ? `Question ${currentQuestionIndex + 1}` : game.title}
                    </h1>
                    {game.difficulty && (
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-medium ${
                          game.difficulty === 'beginner'
                            ? 'bg-green-100 text-green-700'
                            : game.difficulty === 'intermediate'
                            ? 'bg-yellow-100 text-yellow-700'
                            : 'bg-red-100 text-red-700'
                        }`}
                      >
                        {game.difficulty}
                      </span>
                    )}
                  </div>

                  {isMultiQuestion && currentQuestion.concept && (
                    <div className="mb-3 text-sm text-gray-600">
                      <span className="font-medium">Concept:</span> {currentQuestion.concept}
                    </div>
                  )}

                  <div className="prose max-w-none">
                    <p className="text-gray-700 whitespace-pre-wrap mb-4">
                      {currentQuestion.description}
                    </p>

                    {currentQuestion.function_signature && (
                      <div className="bg-gray-50 rounded-lg p-4 mb-4">
                        <p className="text-sm font-medium text-gray-700 mb-2">Function Signature:</p>
                        <code className="text-sm text-purple-600 font-mono">
                          {currentQuestion.function_signature}
                        </code>
                      </div>
                    )}

                    {currentQuestion.test_cases && currentQuestion.test_cases.length > 0 && (
                      <div className="mt-4">
                        <p className="text-sm font-medium text-gray-700 mb-2">Test Cases:</p>
                        <div className="space-y-2">
                          {currentQuestion.test_cases.slice(0, 3).map((testCase: any, idx: number) => (
                            <div key={idx} className="bg-gray-50 rounded p-3 text-sm">
                              <div className="font-medium text-gray-700">Example {idx + 1}:</div>
                              <div className="text-gray-600 mt-1">
                                Input: <code className="text-purple-600">{JSON.stringify(testCase.input)}</code>
                              </div>
                              <div className="text-gray-600">
                                Output: <code className="text-green-600">{JSON.stringify(testCase.expected_output)}</code>
                              </div>
                            </div>
                          ))}
                          {currentQuestion.test_cases.length > 3 && (
                            <div className="text-sm text-gray-500">
                              + {currentQuestion.test_cases.length - 3} more test cases
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Test Results */}
                {testResults.length > 0 && (
                  <div className="bg-white border rounded-xl p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h2 className="text-lg font-bold text-gray-900">Test Results</h2>
                      {allPassed ? (
                        <div className="flex items-center gap-2 text-green-600">
                          <CheckCircle className="h-5 w-5" />
                          <span className="font-medium">All tests passed!</span>
                        </div>
                      ) : (
                        <div className="flex items-center gap-2 text-red-600">
                          <XCircle className="h-5 w-5" />
                          <span className="font-medium">
                            {evaluationResult?.passed_tests || 0} / {evaluationResult?.total_tests || 0} passed
                          </span>
                        </div>
                      )}
                    </div>

                    <div className="space-y-2 max-h-64 overflow-y-auto">
                      {testResults.map((test: any, idx: number) => (
                        <div
                          key={idx}
                          className={`p-3 rounded-lg border ${
                            test.passed
                              ? 'bg-green-50 border-green-200'
                              : 'bg-red-50 border-red-200'
                          }`}
                        >
                          <div className="flex items-center justify-between mb-1">
                            <span className="font-medium text-sm">{test.test_name || `Test ${idx + 1}`}</span>
                            {test.passed ? (
                              <CheckCircle className="h-4 w-4 text-green-600" />
                            ) : (
                              <XCircle className="h-4 w-4 text-red-600" />
                            )}
                          </div>
                          {!test.passed && test.error && (
                            <div className="text-xs text-red-600 mt-1">{test.error}</div>
                          )}
                          {!test.passed && test.expected !== undefined && (
                            <div className="text-xs text-gray-600 mt-1">
                              Expected: <code>{JSON.stringify(test.expected)}</code>
                              {test.actual !== undefined && (
                                <>
                                  {' | '}Got: <code>{JSON.stringify(test.actual)}</code>
                                </>
                              )}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>

                    {evaluationResult?.feedback && (
                      <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                        <p className="text-sm text-blue-800">{evaluationResult.feedback}</p>
                      </div>
                    )}

                    {allPassed && !isMultiQuestion && (
                      <div className="mt-4">
                        {error && (
                          <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded-lg">
                            <p className="text-sm text-red-800">{error}</p>
                          </div>
                        )}
                        <button
                          onClick={handleComplete}
                          disabled={submitting}
                          className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition font-medium flex items-center justify-center gap-2 disabled:opacity-50"
                        >
                          <Trophy className="h-5 w-5" />
                          {submitting ? 'Completing...' : 'Complete Challenge'}
                        </button>
                      </div>
                    )}
                  </div>
                )}

                {/* Question Navigation Buttons */}
                {isMultiQuestion && questions.length > 1 && (
                  <div className="bg-white border rounded-xl p-4">
                    <div className="flex items-center justify-between">
                      <button
                        onClick={() => handleQuestionChange(currentQuestionIndex - 1)}
                        disabled={currentQuestionIndex === 0}
                        className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <ChevronLeft className="h-4 w-4" />
                        Previous
                      </button>
                      <button
                        onClick={() => handleQuestionChange(currentQuestionIndex + 1)}
                        disabled={currentQuestionIndex === questions.length - 1}
                        className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Next
                        <ChevronRight className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                )}

                {/* Complete Button for Multi-Question Games */}
                {isMultiQuestion && allQuestionsCompleted && (
                  <div className="bg-white border rounded-xl p-4">
                    {error && (
                      <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded-lg">
                        <p className="text-sm text-red-800">{error}</p>
                      </div>
                    )}
                    <button
                      onClick={handleComplete}
                      disabled={submitting}
                      className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition font-medium flex items-center justify-center gap-2 disabled:opacity-50"
                    >
                      <Trophy className="h-5 w-5" />
                      {submitting ? 'Completing...' : 'Complete Challenge'}
                    </button>
                  </div>
                )}
              </div>

              {/* Code Editor */}
              <div className="bg-white border rounded-xl p-6">
                <h2 className="text-lg font-bold text-gray-900 mb-4">Your Solution</h2>
                <div className="h-[600px]">
                  <CodeEditor
                    code={currentCode}
                    language={game.game_content?.language || 'python'}
                    onChange={handleCodeChange}
                    onSubmit={handleSubmit}
                    onReset={handleReset}
                    disabled={submitting}
                    loading={submitting}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};
