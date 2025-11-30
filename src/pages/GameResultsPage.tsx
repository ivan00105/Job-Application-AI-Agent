import { useState, useEffect } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import { Layout } from '../components/Layout';
import { gamesAPI, GameResult } from '../api/gamesClient';
import { Trophy, Clock, Award, ArrowRight, Star, Medal } from 'lucide-react';

export const GameResultsPage = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const [result, setResult] = useState<GameResult | null>(location.state?.result || null);
  const [loading, setLoading] = useState(!result);

  useEffect(() => {
    if (!result && sessionId) {
      loadResult();
    }
  }, [sessionId, result]);

  const loadResult = async () => {
    if (!sessionId) return;
    
    try {
      setLoading(true);
      // We fetch session data to reconstruct basic result if state is missing
      const { session } = await gamesAPI.getSession(sessionId);
      
      // Parse result_data if it exists
      const resultData = session.result_data || {};
      
      setResult({
        session: session,
        attempts: [], 
        final_score: session.score || 0,
        badges_earned: [], // Note: We can't easily get badges from just session without a specific endpoint
        leaderboard_position: undefined 
      });
    } catch (err) {
      console.error('Failed to load results:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex justify-center items-center min-h-[60vh]">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
        </div>
      </Layout>
    );
  }

  if (!result) {
    return (
      <Layout>
        <div className="max-w-4xl mx-auto p-6">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-gray-900">Results not found</h2>
            <button
              onClick={() => navigate('/games')}
              className="mt-4 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
            >
              Back to Challenge Center
            </button>
          </div>
        </div>
      </Layout>
    );
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  return (
    <Layout>
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
          {/* Header with Score */}
          <div className="bg-gradient-to-br from-purple-600 to-indigo-600 p-8 text-white text-center">
            <div className="inline-flex p-4 bg-white/10 rounded-full mb-4 backdrop-blur-sm">
              <Trophy className="h-12 w-12 text-yellow-300" />
            </div>
            <h1 className="text-3xl font-bold mb-2">Challenge Completed!</h1>
            <div className="text-6xl font-bold mb-2">{result.final_score}</div>
            <p className="text-purple-100">Total Score</p>
          </div>

          <div className="p-8">
            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <div className="bg-gray-50 rounded-xl p-4 flex items-center gap-4 border border-gray-100">
                <div className="p-3 bg-blue-100 text-blue-600 rounded-lg">
                  <Clock className="h-6 w-6" />
                </div>
                <div>
                  <div className="text-sm text-gray-500">Time Taken</div>
                  <div className="text-xl font-bold text-gray-900">
                    {formatTime(result.session.time_taken_seconds || 0)}
                  </div>
                </div>
              </div>

              <div className="bg-gray-50 rounded-xl p-4 flex items-center gap-4 border border-gray-100">
                <div className="p-3 bg-green-100 text-green-600 rounded-lg">
                  <Award className="h-6 w-6" />
                </div>
                <div>
                  <div className="text-sm text-gray-500">Badges Earned</div>
                  <div className="text-xl font-bold text-gray-900">
                    {result.badges_earned.length}
                  </div>
                </div>
              </div>

              <div className="bg-gray-50 rounded-xl p-4 flex items-center gap-4 border border-gray-100">
                <div className="p-3 bg-yellow-100 text-yellow-600 rounded-lg">
                  <Star className="h-6 w-6" />
                </div>
                <div>
                  <div className="text-sm text-gray-500">Leaderboard Rank</div>
                  <div className="text-xl font-bold text-gray-900">
                    {result.leaderboard_position ? `#${result.leaderboard_position}` : '-'}
                  </div>
                </div>
              </div>
            </div>

            {/* Badges Section */}
            {result.badges_earned.length > 0 && (
              <div className="mb-8">
                <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <Medal className="h-5 w-5 text-purple-600" />
                  New Badges
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {result.badges_earned.map((badge, idx) => (
                    <div key={idx} className="flex items-center gap-3 p-4 bg-yellow-50 border border-yellow-100 rounded-xl">
                      <div className="p-2 bg-yellow-100 rounded-full">
                        <Award className="h-6 w-6 text-yellow-600" />
                      </div>
                      <span className="font-medium text-yellow-900">{badge}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center mt-8">
              <button
                onClick={() => navigate('/games')}
                className="px-6 py-3 bg-gray-100 text-gray-700 rounded-xl hover:bg-gray-200 transition font-medium"
              >
                Back to Challenge Center
              </button>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};

