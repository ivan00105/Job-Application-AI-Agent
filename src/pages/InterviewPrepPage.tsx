import { useState, useEffect } from 'react';
import { Layout } from '../components/Layout';
import { useNavigate } from 'react-router-dom';
import { interviewAPI, StartSessionRequest } from '../api/interviewClient';
import { Brain, Briefcase, TrendingUp, Clock, BookOpen, ArrowRight } from 'lucide-react';

export const InterviewPrepPage = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [analytics, setAnalytics] = useState<any[]>([]);
  const [recentSessions, setRecentSessions] = useState<any[]>([]);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [analyticsData, historyData] = await Promise.all([
        interviewAPI.getAnalytics(),
        interviewAPI.getSessionHistory(5),
      ]);
      setAnalytics(analyticsData);
      setRecentSessions(historyData.sessions);
    } catch (err) {
      console.error('Failed to load data:', err);
    }
  };

  const startNewSession = async (roleType: 'IT' | 'Finance', domain: 'IT' | 'Finance') => {
    setLoading(true);
    try {
      const request: StartSessionRequest = {
        role_type: roleType,
        domain: domain,
        total_questions: 5,
      };
      const session = await interviewAPI.startSession(request);
      navigate(`/interview/session/${session.id}`);
    } catch (err: any) {
      console.error('Failed to start session:', err);
      alert('Failed to start interview session. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout>
      <div className="space-y-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Interview Preparation</h1>
            <p className="text-gray-600 mt-1">
              Practice with AI-powered mock interviews for IT and Finance roles
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-gradient-to-br from-blue-50 to-blue-100 border-2 border-blue-200 rounded-xl p-8 hover:shadow-lg transition">
            <div className="flex items-center mb-4">
              <div className="bg-blue-600 text-white p-3 rounded-lg">
                <Brain className="h-8 w-8" />
              </div>
              <h2 className="text-2xl font-bold text-gray-900 ml-4">IT Roles</h2>
            </div>
            <p className="text-gray-700 mb-6">
              Technical questions, coding challenges, system design, and behavioral scenarios for
              software engineering and tech positions.
            </p>
            <button
              onClick={() => startNewSession('IT', 'IT')}
              disabled={loading}
              className="w-full bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition flex items-center justify-center disabled:opacity-50"
            >
              Start IT Interview
              <ArrowRight className="ml-2 h-5 w-5" />
            </button>
          </div>

          <div className="bg-gradient-to-br from-green-50 to-green-100 border-2 border-green-200 rounded-xl p-8 hover:shadow-lg transition">
            <div className="flex items-center mb-4">
              <div className="bg-green-600 text-white p-3 rounded-lg">
                <TrendingUp className="h-8 w-8" />
              </div>
              <h2 className="text-2xl font-bold text-gray-900 ml-4">Finance Roles</h2>
            </div>
            <p className="text-gray-700 mb-6">
              Financial analysis, case studies, market scenarios, and technical questions for
              finance, accounting, and investment positions.
            </p>
            <button
              onClick={() => startNewSession('Finance', 'Finance')}
              disabled={loading}
              className="w-full bg-green-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-green-700 transition flex items-center justify-center disabled:opacity-50"
            >
              Start Finance Interview
              <ArrowRight className="ml-2 h-5 w-5" />
            </button>
          </div>
        </div>

        {analytics.length > 0 && (
          <div className="bg-white border rounded-xl p-6">
            <div className="flex items-center mb-4">
              <BookOpen className="h-6 w-6 text-gray-600 mr-2" />
              <h2 className="text-xl font-bold text-gray-900">Your Performance</h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {analytics.map((stat) => (
                <div key={stat.domain} className="bg-gray-50 rounded-lg p-4">
                  <div className="text-sm text-gray-600 mb-1">{stat.domain}</div>
                  <div className="text-2xl font-bold text-gray-900">
                    {stat.avg_overall_score ? (stat.avg_overall_score * 20).toFixed(0) : '0'}%
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    {stat.total_sessions} sessions • {stat.total_questions_answered} questions
                  </div>
                </div>
              ))}
            </div>
            <button
              onClick={() => navigate('/interview/analytics')}
              className="mt-4 text-blue-600 hover:text-blue-700 font-medium flex items-center"
            >
              View detailed analytics
              <ArrowRight className="ml-1 h-4 w-4" />
            </button>
          </div>
        )}

        {recentSessions.length > 0 && (
          <div className="bg-white border rounded-xl p-6">
            <div className="flex items-center mb-4">
              <Clock className="h-6 w-6 text-gray-600 mr-2" />
              <h2 className="text-xl font-bold text-gray-900">Recent Practice Sessions</h2>
            </div>
            <div className="space-y-3">
              {recentSessions.map((session) => (
                <div
                  key={session.id}
                  className="flex items-center justify-between bg-gray-50 rounded-lg p-4 hover:bg-gray-100 transition cursor-pointer"
                  onClick={() => navigate(`/interview/session/${session.id}/results`)}
                >
                  <div className="flex items-center">
                    <Briefcase className="h-5 w-5 text-gray-600 mr-3" />
                    <div>
                      <div className="font-medium text-gray-900">
                        {session.domain} Interview
                      </div>
                      <div className="text-sm text-gray-500">
                        {new Date(session.started_at).toLocaleDateString()} •{' '}
                        {session.completed_questions}/{session.total_questions} completed
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center">
                    {session.avg_score && (
                      <div className="text-lg font-bold text-gray-900 mr-3">
                        {(session.avg_score * 20).toFixed(0)}%
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

        <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">How it works</h3>
          <ul className="space-y-2 text-gray-700">
            <li className="flex items-start">
              <span className="font-bold mr-2">1.</span>
              Choose your role type (IT or Finance) to start a practice session
            </li>
            <li className="flex items-start">
              <span className="font-bold mr-2">2.</span>
              Answer 5 realistic interview questions at your own pace
            </li>
            <li className="flex items-start">
              <span className="font-bold mr-2">3.</span>
              Get instant AI feedback with scores and improvement suggestions
            </li>
            <li className="flex items-start">
              <span className="font-bold mr-2">4.</span>
              Track your progress and identify areas to improve
            </li>
          </ul>
        </div>
      </div>
    </Layout>
  );
};
