import { useState, useEffect } from 'react';
import { Layout } from '../components/Layout';
import { useParams, useNavigate } from 'react-router-dom';
import { gamesAPI, Game, GameSession, GameAttempt } from '../api/gamesClient';
import { ArrowLeft, CheckCircle, XCircle, Clock, Trophy, ChevronLeft, ChevronRight } from 'lucide-react';

interface MCQuestion {
  question_text: string;
  options: Array<{ id: string; text: string }>;
  correct_answer: string;
  explanation?: string;
  question_number?: number;
  points?: number;
}

export const MultipleChoicePage = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [game, setGame] = useState<Game | null>(null);
  const [session, setSession] = useState<GameSession | null>(null);
  
  // Question state
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<number, string>>({});
  const [questionAttempts, setQuestionAttempts] = useState<Record<number, GameAttempt | null>>({});
  const [questionProgress, setQuestionProgress] = useState<Record<number, { passed: boolean; score: number }>>({});
  
  const [timeElapsed, setTimeElapsed] = useState(0);
  const [error, setError] = useState<string | null>(null);

  // Check if game has multiple questions
  const isMultiQuestion = game?.game_content?.questions && Array.isArray(game.game_content.questions);
  const questions: MCQuestion[] = isMultiQuestion 
    ? game.game_content.questions 
    : game?.game_content 
      ? [{
          question_text: game.game_content.question || game.description || '',
          options: game.game_content.options || [],
          correct_answer: game.game_content.correct_answer || '',
          explanation: game.game_content.explanation
        }]
      : [];
  
  const currentQuestion = questions[currentQuestionIndex];
  const currentAnswer = selectedAnswers[currentQuestionIndex] || '';
  const currentAttempt = questionAttempts[currentQuestionIndex] || null;

  useEffect(() => {
    if (sessionId) {
      loadSession();
    }
  }, [sessionId]);

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
      setError('Failed to load challenge session. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleAnswerSelect = (answerId: string) => {
    setSelectedAnswers(prev => ({
      ...prev,
      [currentQuestionIndex]: answerId
    }));
    setError(null);
  };

  const handleSubmit = async () => {
    if (!sessionId || !currentAnswer || !currentQuestion) return;

    setSubmitting(true);
    setError(null);
    try {
      const answerData: any = {
        selected_answer: currentAnswer,
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
            passed: evalResult.is_correct || false,
            score: evalResult.is_correct ? (currentQuestion.points || 10) : 0
          }
        }));
      }
    } catch (err: any) {
      console.error('Failed to submit:', err);
      setError(err?.response?.data?.detail || 'Failed to submit answer. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleQuestionChange = (newIndex: number) => {
    if (newIndex >= 0 && newIndex < questions.length) {
      setCurrentQuestionIndex(newIndex);
      setError(null);
    }
  };

  const handleComplete = async () => {
    if (!sessionId) return;
    
    setSubmitting(true);
    setError(null);
    try {
      const result = await gamesAPI.completeSession(sessionId);
      navigate(`/games/results/${sessionId}`);
    } catch (err: any) {
      console.error('Failed to complete:', err);
      setError(err?.response?.data?.detail || 'Failed to complete challenge. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const allQuestionsAnswered = questions.every((_, idx) => selectedAnswers[idx]);
  const allQuestionsSubmitted = questions.every((_, idx) => questionAttempts[idx] !== null);
  const totalScore = Object.values(questionProgress).reduce((sum, p) => sum + p.score, 0);
  const maxScore = questions.reduce((sum, q) => sum + (q.points || 10), 0);

  // Show loading state
  if (loading) {
    return (
      <Layout>
        <div className="max-w-4xl mx-auto">
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
            <p className="mt-4 text-gray-600">Loading challenge...</p>
          </div>
        </div>
      </Layout>
    );
  }

  if (!game || !session) {
    return (
      <Layout>
        <div className="max-w-4xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
            <p className="text-red-800">Failed to load challenge. Please try again.</p>
            <button
              onClick={() => navigate('/games')}
              className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
            >
              Back to Challenge Center
            </button>
          </div>
        </div>
      </Layout>
    );
  }

  if (questions.length === 0) {
    return (
      <Layout>
        <div className="max-w-4xl mx-auto">
          <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-6 text-center">
            <p className="text-yellow-800 mb-2">No questions available for this challenge.</p>
            <p className="text-sm text-yellow-700 mb-4">
              The challenge may not have questions configured yet, or there was an error loading them.
            </p>
            <div className="text-xs text-gray-600 mb-4 p-3 bg-white rounded border">
              <p>Game Type: {game.game_type}</p>
              <p>Game Content Keys: {Object.keys(game.game_content || {}).join(', ')}</p>
              {game.game_content?.questions && (
                <p>Questions Array Length: {Array.isArray(game.game_content.questions) ? game.game_content.questions.length : 'Not an array'}</p>
              )}
            </div>
            <button
              onClick={() => navigate('/games')}
              className="mt-4 px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700"
            >
              Back to Challenge Center
            </button>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <button
            onClick={() => navigate('/games')}
            className="flex items-center text-gray-600 hover:text-gray-900"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Challenge Center
          </button>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <Clock className="h-4 w-4" />
              <span>{formatTime(timeElapsed)}</span>
            </div>
            <div className="text-sm text-gray-600">
              Score: <span className="font-bold text-purple-600">{totalScore}</span> / {maxScore}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Question Navigation Sidebar */}
          {isMultiQuestion && questions.length > 1 && (
            <div className="lg:col-span-1">
              <div className="bg-white border rounded-xl p-4 sticky top-4">
                <h3 className="font-semibold text-gray-900 mb-3">Questions</h3>
                <div className="space-y-2">
                  {questions.map((q, idx) => {
                    const isAnswered = !!selectedAnswers[idx];
                    const isSubmitted = !!questionAttempts[idx];
                    const isPassed = questionProgress[idx]?.passed;
                    const isCurrent = idx === currentQuestionIndex;
                    
                    return (
                      <button
                        key={idx}
                        onClick={() => handleQuestionChange(idx)}
                        className={`w-full text-left p-2 rounded-lg text-sm transition ${
                          isCurrent
                            ? 'bg-purple-100 border-2 border-purple-600'
                            : 'bg-gray-50 border border-gray-200 hover:bg-gray-100'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-medium">Q{idx + 1}</span>
                          <div className="flex items-center gap-1">
                            {isSubmitted && (
                              isPassed ? (
                                <CheckCircle className="h-4 w-4 text-green-600" />
                              ) : (
                                <XCircle className="h-4 w-4 text-red-600" />
                              )
                            )}
                            {isAnswered && !isSubmitted && (
                              <div className="h-2 w-2 rounded-full bg-blue-500" />
                            )}
                          </div>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {/* Main Content */}
          <div className={isMultiQuestion && questions.length > 1 ? "lg:col-span-3" : "lg:col-span-4"}>
            <div className="bg-white border rounded-xl p-6 space-y-6">
              {/* Question Header */}
              <div className="flex items-center justify-between">
                <div>
                  {isMultiQuestion && (
                    <div className="text-sm text-gray-600 mb-2">
                      Question {currentQuestionIndex + 1} of {questions.length}
                    </div>
                  )}
                  <h2 className="text-2xl font-bold text-gray-900">Question</h2>
                </div>
                {currentQuestion.points && (
                  <div className="text-sm text-gray-600">
                    <span className="font-medium">Points:</span> {currentQuestion.points}
                  </div>
                )}
              </div>

              {/* Error Display */}
              {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                  <p className="text-sm text-red-800">{error}</p>
                </div>
              )}

              {/* Question Text */}
              <div className="prose max-w-none">
                <p className="text-lg text-gray-800 leading-relaxed">
                  {currentQuestion.question_text}
                </p>
              </div>

              {/* Answer Options */}
              <div className="space-y-3">
                {currentQuestion.options.map((option) => {
                  const isSelected = currentAnswer === option.id;
                  const isSubmitted = currentAttempt !== null;
                  const isCorrect = option.id === currentQuestion.correct_answer;
                  const showResult = isSubmitted;
                  
                  let optionClass = "w-full text-left p-4 rounded-lg border-2 transition cursor-pointer ";
                  if (showResult) {
                    if (isCorrect) {
                      optionClass += "bg-green-50 border-green-500 text-green-900";
                    } else if (isSelected && !isCorrect) {
                      optionClass += "bg-red-50 border-red-500 text-red-900";
                    } else {
                      optionClass += "bg-gray-50 border-gray-200 text-gray-700";
                    }
                  } else {
                    optionClass += isSelected
                      ? "bg-purple-50 border-purple-500 text-purple-900"
                      : "bg-white border-gray-300 hover:border-purple-400 hover:bg-purple-50 text-gray-800";
                  }

                  return (
                    <button
                      key={option.id}
                      onClick={() => !showResult && handleAnswerSelect(option.id)}
                      disabled={showResult || submitting}
                      className={optionClass}
                    >
                      <div className="flex items-center gap-3">
                        <div className={`flex-shrink-0 w-6 h-6 rounded-full border-2 flex items-center justify-center ${
                          isSelected
                            ? showResult && isCorrect
                              ? "bg-green-500 border-green-600"
                              : showResult && !isCorrect
                              ? "bg-red-500 border-red-600"
                              : "bg-purple-500 border-purple-600"
                            : "border-gray-300"
                        }`}>
                          {isSelected && (
                            <div className="w-2 h-2 rounded-full bg-white" />
                          )}
                        </div>
                        <span className="font-medium mr-2">{option.id.toUpperCase()}.</span>
                        <span className="flex-1">{option.text}</span>
                        {showResult && isCorrect && (
                          <CheckCircle className="h-5 w-5 text-green-600 flex-shrink-0" />
                        )}
                        {showResult && isSelected && !isCorrect && (
                          <XCircle className="h-5 w-5 text-red-600 flex-shrink-0" />
                        )}
                      </div>
                    </button>
                  );
                })}
              </div>

              {/* Explanation */}
              {currentAttempt && currentQuestion.explanation && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h4 className="font-semibold text-blue-900 mb-2">Explanation:</h4>
                  <p className="text-sm text-blue-800">{currentQuestion.explanation}</p>
                </div>
              )}

              {/* Navigation and Actions */}
              <div className="flex items-center justify-between pt-4 border-t">
                <div className="flex gap-2">
                  {isMultiQuestion && (
                    <>
                      <button
                        onClick={() => handleQuestionChange(currentQuestionIndex - 1)}
                        disabled={currentQuestionIndex === 0}
                        className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                      >
                        <ChevronLeft className="h-4 w-4" />
                        Previous
                      </button>
                      <button
                        onClick={() => handleQuestionChange(currentQuestionIndex + 1)}
                        disabled={currentQuestionIndex === questions.length - 1}
                        className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                      >
                        Next
                        <ChevronRight className="h-4 w-4" />
                      </button>
                    </>
                  )}
                </div>

                <div className="flex gap-2">
                  {!currentAttempt && (
                    <button
                      onClick={handleSubmit}
                      disabled={!currentAnswer || submitting}
                      className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {submitting ? 'Submitting...' : 'Submit Answer'}
                    </button>
                  )}
                  {isMultiQuestion && allQuestionsSubmitted && (
                    <button
                      onClick={handleComplete}
                      disabled={submitting}
                      className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                      <Trophy className="h-4 w-4" />
                      Complete Challenge
                    </button>
                  )}
                  {!isMultiQuestion && currentAttempt && (
                    <button
                      onClick={handleComplete}
                      disabled={submitting}
                      className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                      <Trophy className="h-4 w-4" />
                      Complete Challenge
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};

