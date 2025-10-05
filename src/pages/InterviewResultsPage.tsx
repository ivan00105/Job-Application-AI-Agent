import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Layout } from '../components/Layout';
import { interviewAPI, SessionDetail } from '../api/interviewClient';
import { TrendingUp, CheckCircle, Award, ArrowLeft, Home } from 'lucide-react';

export const InterviewResultsPage = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [sessionDetail, setSessionDetail] = useState<SessionDetail | null>(null);

  useEffect(() => {
    if (sessionId) {
      loadSessionDetail();
    }
  }, [sessionId]);

  const loadSessionDetail = async () => {
    try {
      const detail = await interviewAPI.getSessionDetail(sessionId!);
      setSessionDetail(detail);
    } catch (err) {
      console.error('Failed to load session detail:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="text-center py-20">
          <div className="text-gray-500">Loading results...</div>
        </div>
      </Layout>
    );
  }

  if (!sessionDetail) {
    return (
      <Layout>
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <p className="text-red-800">Session not found.</p>
        </div>
      </Layout>
    );
  }

  const { session, responses, questions } = sessionDetail;
  const overallPercentage = session.avg_score ? (session.avg_score / 5) * 100 : 0;

  const getQuestionById = (questionId: string) => {
    return questions.find((q) => q.id === questionId);
  };

  return (
    <Layout>
      <div className="max-w-5xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <button
            onClick={() => navigate('/interview')}
            className="flex items-center text-gray-600 hover:text-gray-900"
          >
            <ArrowLeft className="h-5 w-5 mr-2" />
            Back to Interview Prep
          </button>
        </div>

        <div className="bg-gradient-to-br from-blue-50 to-blue-100 border-2 border-blue-200 rounded-xl p-8">
          <div className="flex items-center mb-4">
            <Award className="h-12 w-12 text-blue-600 mr-4" />
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Session Complete!</h1>
              <p className="text-gray-600 mt-1">
                {session.domain} Interview • {session.completed_questions} questions answered
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6">
            <div className="bg-white rounded-lg p-6 text-center">
              <div className="text-4xl font-bold text-blue-600 mb-2">
                {overallPercentage.toFixed(0)}%
              </div>
              <div className="text-sm text-gray-600">Overall Score</div>
            </div>

            <div className="bg-white rounded-lg p-6 text-center">
              <div className="text-4xl font-bold text-green-600 mb-2">
                {session.completed_questions}
              </div>
              <div className="text-sm text-gray-600">Questions Answered</div>
            </div>

            <div className="bg-white rounded-lg p-6 text-center">
              <div className="text-4xl font-bold text-gray-900 mb-2">
                {session.avg_score?.toFixed(1) || 'N/A'}
              </div>
              <div className="text-sm text-gray-600">Avg Score (1-5)</div>
            </div>
          </div>
        </div>

        <div className="bg-white border rounded-lg p-6">
          <div className="flex items-center mb-6">
            <CheckCircle className="h-6 w-6 text-green-600 mr-2" />
            <h2 className="text-xl font-bold text-gray-900">Question-by-Question Breakdown</h2>
          </div>

          <div className="space-y-6">
            {responses.map((response, idx) => {
              const question = getQuestionById(response.question_id);
              const scores = response.evaluation_scores;

              return (
                <div key={response.id} className="border-b pb-6 last:border-b-0">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="font-bold text-gray-900">Question {idx + 1}</span>
                        <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs font-medium rounded">
                          {question?.category}
                        </span>
                        <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs font-medium rounded">
                          {question?.difficulty}
                        </span>
                      </div>
                      <p className="text-gray-900 font-medium">{question?.question_text}</p>
                    </div>
                    {scores && (
                      <div className="ml-4 text-right">
                        <div className="text-2xl font-bold text-blue-600">
                          {((scores.overall_score / 5) * 100).toFixed(0)}%
                        </div>
                        <div className="text-xs text-gray-500">Overall</div>
                      </div>
                    )}
                  </div>

                  <div className="bg-gray-50 rounded-lg p-4 mb-3">
                    <div className="text-sm text-gray-600 font-medium mb-1">Your Answer:</div>
                    <p className="text-gray-800 text-sm">{response.user_answer}</p>
                  </div>

                  {response.feedback && (
                    <div className="bg-blue-50 rounded-lg p-4 mb-3">
                      <div className="text-sm text-gray-900 font-medium mb-1">Feedback:</div>
                      <p className="text-gray-700 text-sm">{response.feedback}</p>
                    </div>
                  )}

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {response.strengths.length > 0 && (
                      <div>
                        <div className="text-sm font-medium text-green-700 mb-1">Strengths:</div>
                        <ul className="space-y-1">
                          {response.strengths.map((s, i) => (
                            <li key={i} className="text-sm text-gray-600 flex items-start">
                              <span className="text-green-600 mr-1">✓</span>
                              {s}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {response.improvements.length > 0 && (
                      <div>
                        <div className="text-sm font-medium text-blue-700 mb-1">
                          Areas to Improve:
                        </div>
                        <ul className="space-y-1">
                          {response.improvements.map((i, idx) => (
                            <li key={idx} className="text-sm text-gray-600 flex items-start">
                              <span className="text-blue-600 mr-1">→</span>
                              {i}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="flex gap-4">
          <button
            onClick={() => navigate('/interview')}
            className="flex-1 bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition flex items-center justify-center"
          >
            <TrendingUp className="mr-2 h-5 w-5" />
            Practice Again
          </button>
          <button
            onClick={() => navigate('/interview/analytics')}
            className="flex-1 bg-gray-100 text-gray-900 px-6 py-3 rounded-lg font-semibold hover:bg-gray-200 transition flex items-center justify-center"
          >
            View Analytics
          </button>
        </div>
      </div>
    </Layout>
  );
};
