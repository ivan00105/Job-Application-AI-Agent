import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Layout } from '../components/Layout';
import { interviewAPI, QuestionWithContext, EvaluationResult } from '../api/interviewClient';
import {
  ArrowRight,
  CheckCircle,
  TrendingUp,
  AlertCircle,
  Loader,
  MessageSquare,
  ThumbsUp,
  Target,
} from 'lucide-react';

export const InterviewSessionPage = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [currentQuestion, setCurrentQuestion] = useState<QuestionWithContext | null>(null);
  const [answer, setAnswer] = useState('');
  const [evaluation, setEvaluation] = useState<EvaluationResult | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (sessionId) {
      loadNextQuestion();
    }
  }, [sessionId]);

  const loadNextQuestion = async () => {
    setLoading(true);
    setEvaluation(null);
    setAnswer('');
    setError('');
    try {
      const question = await interviewAPI.getNextQuestion(sessionId!);
      setCurrentQuestion(question);
    } catch (err: any) {
      if (err.response?.status === 400) {
        navigate(`/interview/session/${sessionId}/results`);
      } else {
        setError('Failed to load question. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!answer.trim() || answer.length < 10) {
      alert('Please provide a more detailed answer (at least 10 characters).');
      return;
    }

    setSubmitting(true);
    try {
      const result = await interviewAPI.submitAnswer(
        sessionId!,
        currentQuestion!.question.id,
        answer
      );
      setEvaluation(result);
    } catch (err) {
      console.error('Failed to submit answer:', err);
      alert('Failed to submit answer. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleNext = () => {
    if (evaluation?.is_session_complete) {
      navigate(`/interview/session/${sessionId}/results`);
    } else {
      loadNextQuestion();
    }
  };

  const renderScoreBar = (score: number, label: string) => {
    const percentage = (score / 5) * 100;
    const color =
      percentage >= 80
        ? 'bg-green-500'
        : percentage >= 60
        ? 'bg-blue-500'
        : percentage >= 40
        ? 'bg-yellow-500'
        : 'bg-red-500';

    return (
      <div className="mb-3">
        <div className="flex justify-between text-sm mb-1">
          <span className="text-gray-700">{label}</span>
          <span className="font-semibold text-gray-900">{score.toFixed(1)}/5</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div className={`${color} h-2 rounded-full transition-all`} style={{ width: `${percentage}%` }}></div>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center py-20">
          <Loader className="h-8 w-8 animate-spin text-blue-600" />
          <span className="ml-3 text-gray-600">Loading question...</span>
        </div>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout>
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <AlertCircle className="h-6 w-6 text-red-600 mb-2" />
          <p className="text-red-800">{error}</p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-4xl mx-auto space-y-6">
        {currentQuestion && (
          <>
            <div className="bg-white border rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center">
                  <MessageSquare className="h-5 w-5 text-blue-600 mr-2" />
                  <span className="text-sm font-medium text-gray-600">
                    Question {currentQuestion.question_number} of {currentQuestion.total_questions}
                  </span>
                </div>
                <div className="text-sm text-gray-600">
                  Progress: {currentQuestion.session_progress.toFixed(0)}%
                </div>
              </div>

              <div className="w-full bg-gray-200 rounded-full h-2 mb-6">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all"
                  style={{ width: `${currentQuestion.session_progress}%` }}
                ></div>
              </div>

              <div className="mb-4">
                <div className="flex gap-2 mb-3">
                  <span className="px-3 py-1 bg-blue-100 text-blue-700 text-xs font-medium rounded-full">
                    {currentQuestion.question.category}
                  </span>
                  <span className="px-3 py-1 bg-gray-100 text-gray-700 text-xs font-medium rounded-full">
                    {currentQuestion.question.difficulty}
                  </span>
                </div>
                <h2 className="text-2xl font-bold text-gray-900">
                  {currentQuestion.question.question_text}
                </h2>
              </div>

              {!evaluation ? (
                <>
                  <textarea
                    value={answer}
                    onChange={(e) => setAnswer(e.target.value)}
                    placeholder="Type your answer here... (minimum 10 characters)"
                    className="w-full h-48 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                    disabled={submitting}
                  />
                  <div className="flex items-center justify-between mt-4">
                    <span className="text-sm text-gray-500">{answer.length} characters</span>
                    <button
                      onClick={handleSubmit}
                      disabled={submitting || answer.length < 10}
                      className="bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition disabled:opacity-50 flex items-center"
                    >
                      {submitting ? (
                        <>
                          <Loader className="animate-spin h-5 w-5 mr-2" />
                          Evaluating...
                        </>
                      ) : (
                        <>
                          Submit Answer
                          <ArrowRight className="ml-2 h-5 w-5" />
                        </>
                      )}
                    </button>
                  </div>
                </>
              ) : (
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="text-sm text-gray-600 font-medium mb-2">Your Answer:</div>
                  <div className="text-gray-800 whitespace-pre-wrap">{answer}</div>
                </div>
              )}
            </div>

            {evaluation && (
              <div className="bg-white border rounded-lg p-6 space-y-6">
                <div className="flex items-center">
                  <CheckCircle className="h-6 w-6 text-green-600 mr-2" />
                  <h3 className="text-xl font-bold text-gray-900">AI Evaluation</h3>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-3">Score Breakdown</h4>
                    {evaluation.response.evaluation_scores && (
                      <>
                        {renderScoreBar(
                          evaluation.response.evaluation_scores.overall_score,
                          'Overall Score'
                        )}
                        {renderScoreBar(
                          evaluation.response.evaluation_scores.relevance_score,
                          'Relevance'
                        )}
                        {renderScoreBar(
                          evaluation.response.evaluation_scores.completeness_score,
                          'Completeness'
                        )}
                        {renderScoreBar(
                          evaluation.response.evaluation_scores.technical_accuracy_score,
                          'Technical Accuracy'
                        )}
                        {renderScoreBar(
                          evaluation.response.evaluation_scores.communication_score,
                          'Communication'
                        )}
                      </>
                    )}
                  </div>

                  <div>
                    <div className="mb-4">
                      <div className="flex items-center mb-2">
                        <ThumbsUp className="h-5 w-5 text-green-600 mr-2" />
                        <h4 className="font-semibold text-gray-900">Strengths</h4>
                      </div>
                      <ul className="space-y-1">
                        {evaluation.response.strengths.map((strength, idx) => (
                          <li key={idx} className="text-sm text-gray-700 flex items-start">
                            <span className="text-green-600 mr-2">•</span>
                            {strength}
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div>
                      <div className="flex items-center mb-2">
                        <Target className="h-5 w-5 text-blue-600 mr-2" />
                        <h4 className="font-semibold text-gray-900">Areas to Improve</h4>
                      </div>
                      <ul className="space-y-1">
                        {evaluation.response.improvements.map((improvement, idx) => (
                          <li key={idx} className="text-sm text-gray-700 flex items-start">
                            <span className="text-blue-600 mr-2">•</span>
                            {improvement}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>

                {evaluation.response.feedback && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <h4 className="font-semibold text-gray-900 mb-2">Detailed Feedback</h4>
                    <p className="text-gray-700">{evaluation.response.feedback}</p>
                  </div>
                )}

                <button
                  onClick={handleNext}
                  className="w-full bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition flex items-center justify-center"
                >
                  {evaluation.is_session_complete ? (
                    <>
                      View Results
                      <TrendingUp className="ml-2 h-5 w-5" />
                    </>
                  ) : (
                    <>
                      Next Question
                      <ArrowRight className="ml-2 h-5 w-5" />
                    </>
                  )}
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </Layout>
  );
};
