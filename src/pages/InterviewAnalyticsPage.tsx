import { useState, useEffect } from 'react';
import { Layout } from '../components/Layout';
import { useNavigate } from 'react-router-dom';
import { interviewAPI, PerformanceAnalytics, SessionHistory } from '../api/interviewClient';
import {
  TrendingUp,
  TrendingDown,
  BarChart3,
  Clock,
  Target,
  ArrowLeft,
  Calendar,
} from 'lucide-react';

export const InterviewAnalyticsPage = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [analytics, setAnalytics] = useState<PerformanceAnalytics[]>([]);
  const [history, setHistory] = useState<SessionHistory | null>(null);

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    try {
      const [analyticsData, historyData] = await Promise.all([
        interviewAPI.getAnalytics(),
        interviewAPI.getSessionHistory(20),
      ]);
      setAnalytics(analyticsData);
      setHistory(historyData);
    } catch (err) {
      console.error('Failed to load analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="text-center py-20">
          <div className="text-gray-500">Loading analytics...</div>
        </div>
      </Layout>
    );
  }

  const renderScoreCard = (
    title: string,
    score: number | undefined,
    icon: React.ReactNode
  ) => {
    const percentage = score ? (score / 5) * 100 : 0;
    const color =
      percentage >= 80
        ? 'text-green-600'
        : percentage >= 60
        ? 'text-blue-600'
        : percentage >= 40
        ? 'text-yellow-600'
        : 'text-red-600';

    return (
      <div className="bg-white border rounded-lg p-6">
        <div className="flex items-center justify-between mb-3">
          <div className="text-sm text-gray-600 font-medium">{title}</div>
          {icon}
        </div>
        <div className={`text-3xl font-bold ${color}`}>
          {score ? percentage.toFixed(0) : '0'}%
        </div>
        <div className="text-xs text-gray-500 mt-1">
          {score ? `${score.toFixed(1)}/5.0` : 'No data yet'}
        </div>
      </div>
    );
  };

  return (
    <Layout>
      <div className="space-y-8">
        <div className="flex items-center justify-between">
          <div>
            <button
              onClick={() => navigate('/interviews')}
              className="flex items-center text-gray-600 hover:text-gray-900 mb-2"
            >
              <ArrowLeft className="h-5 w-5 mr-2" />
              Back
            </button>
            <h1 className="text-3xl font-bold text-gray-900">Performance Analytics</h1>
            <p className="text-gray-600 mt-1">Track your interview preparation progress</p>
          </div>
        </div>

        {analytics.length === 0 ? (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-8 text-center">
            <BarChart3 className="h-12 w-12 text-blue-600 mx-auto mb-3" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No data yet</h3>
            <p className="text-gray-600 mb-4">
              Complete some interview practice sessions to see your analytics.
            </p>
            <button
              onClick={() => navigate('/interviews')}
              className="bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition"
            >
              Start Practicing
            </button>
          </div>
        ) : (
          <>
            {analytics.map((stat) => (
              <div key={stat.domain} className="space-y-6">
                <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-xl p-6">
                  <h2 className="text-2xl font-bold mb-2">{stat.domain} Domain</h2>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <div className="opacity-80">Total Sessions</div>
                      <div className="text-2xl font-bold">{stat.total_sessions}</div>
                    </div>
                    <div>
                      <div className="opacity-80">Questions Answered</div>
                      <div className="text-2xl font-bold">{stat.total_questions_answered}</div>
                    </div>
                    <div>
                      <div className="opacity-80">Last Practice</div>
                      <div className="text-lg font-semibold">
                        {stat.last_practice_date
                          ? new Date(stat.last_practice_date).toLocaleDateString()
                          : 'N/A'}
                      </div>
                    </div>
                    <div>
                      <div className="opacity-80">Overall Score</div>
                      <div className="text-2xl font-bold">
                        {stat.avg_overall_score
                          ? `${((stat.avg_overall_score / 5) * 100).toFixed(0)}%`
                          : 'N/A'}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  {renderScoreCard(
                    'Relevance',
                    stat.avg_relevance_score,
                    <Target className="h-5 w-5 text-blue-600" />
                  )}
                  {renderScoreCard(
                    'Completeness',
                    stat.avg_completeness_score,
                    <BarChart3 className="h-5 w-5 text-green-600" />
                  )}
                  {renderScoreCard(
                    'Technical Accuracy',
                    stat.avg_technical_accuracy_score,
                    <TrendingUp className="h-5 w-5 text-purple-600" />
                  )}
                  {renderScoreCard(
                    'Communication',
                    stat.avg_communication_score,
                    <TrendingUp className="h-5 w-5 text-orange-600" />
                  )}
                </div>

                {(stat.strong_categories.length > 0 || stat.weak_categories.length > 0) && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {stat.strong_categories.length > 0 && (
                      <div className="bg-green-50 border border-green-200 rounded-lg p-6">
                        <div className="flex items-center mb-3">
                          <TrendingUp className="h-5 w-5 text-green-600 mr-2" />
                          <h3 className="font-semibold text-gray-900">Strong Areas</h3>
                        </div>
                        <ul className="space-y-1">
                          {stat.strong_categories.map((cat, idx) => (
                            <li key={idx} className="text-gray-700 flex items-center">
                              <span className="text-green-600 mr-2">✓</span>
                              {cat}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {stat.weak_categories.length > 0 && (
                      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
                        <div className="flex items-center mb-3">
                          <TrendingDown className="h-5 w-5 text-yellow-600 mr-2" />
                          <h3 className="font-semibold text-gray-900">Areas to Improve</h3>
                        </div>
                        <ul className="space-y-1">
                          {stat.weak_categories.map((cat, idx) => (
                            <li key={idx} className="text-gray-700 flex items-center">
                              <span className="text-yellow-600 mr-2">→</span>
                              {cat}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}

            {history && history.sessions.length > 0 && (
              <div className="bg-white border rounded-lg p-6">
                <div className="flex items-center mb-4">
                  <Clock className="h-6 w-6 text-gray-600 mr-2" />
                  <h2 className="text-xl font-bold text-gray-900">Practice History</h2>
                </div>

                <div className="space-y-2">
                  {history.sessions.map((session) => (
                    <div
                      key={session.id}
                      className="flex items-center justify-between bg-gray-50 rounded-lg p-4 hover:bg-gray-100 transition cursor-pointer"
                      onClick={() => navigate(`/interview/session/${session.id}/results`)}
                    >
                      <div className="flex items-center">
                        <Calendar className="h-5 w-5 text-gray-600 mr-3" />
                        <div>
                          <div className="font-medium text-gray-900">
                            {session.domain} Interview
                          </div>
                          <div className="text-sm text-gray-500">
                            {new Date(session.started_at).toLocaleDateString()} •{' '}
                            {session.completed_questions}/{session.total_questions} questions
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        {session.avg_score && (
                          <div className="text-lg font-bold text-gray-900">
                            {((session.avg_score / 5) * 100).toFixed(0)}%
                          </div>
                        )}
                        <div
                          className={`px-3 py-1 rounded-full text-xs font-medium ${
                            session.status === 'completed'
                              ? 'bg-green-100 text-green-700'
                              : session.status === 'active'
                              ? 'bg-blue-100 text-blue-700'
                              : 'bg-gray-100 text-gray-700'
                          }`}
                        >
                          {session.status}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </Layout>
  );
};
