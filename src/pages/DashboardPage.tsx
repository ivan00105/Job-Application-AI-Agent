/**
 * Dashboard Page - Job Matches
 */
import { useState, useEffect } from 'react';
import { Layout } from '../components/Layout';
import { matchesAPI } from '../api/client';
import { Target, TrendingUp, AlertCircle } from 'lucide-react';

export const DashboardPage = () => {
  const [matches, setMatches] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadMatches();
  }, []);

  const loadMatches = async () => {
    try {
      const data = await matchesAPI.getMatches();
      setMatches(data.matches || []);
    } catch (err: any) {
      if (err.response?.status === 404) {
        setError('Please upload your CV first to see job matches.');
      } else {
        setError('Failed to load matches');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Job Matches</h1>
            <p className="text-gray-600 mt-1">AI-powered job recommendations for you</p>
          </div>
        </div>

        {loading ? (
          <div className="text-center py-12">
            <div className="text-gray-500">Loading matches...</div>
          </div>
        ) : error ? (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 flex items-start">
            <AlertCircle className="h-6 w-6 text-yellow-600 mr-3 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="text-lg font-medium text-yellow-900">No matches yet</h3>
              <p className="text-yellow-700 mt-1">{error}</p>
              <a
                href="/profile"
                className="inline-block mt-3 text-yellow-700 underline hover:text-yellow-900"
              >
                Go to CV Upload →
              </a>
            </div>
          </div>
        ) : matches.length === 0 ? (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 text-center">
            <Target className="h-12 w-12 text-blue-600 mx-auto mb-3" />
            <h3 className="text-lg font-medium text-blue-900">Ready to find matches!</h3>
            <p className="text-blue-700 mt-1">
              Job matching algorithm will be implemented in the AI phase.
            </p>
          </div>
        ) : (
          <div className="grid gap-4">
            {matches.map((match: any) => (
              <div key={match.id} className="bg-white border rounded-lg p-6 hover:shadow-md transition">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="text-xl font-semibold text-gray-900">{match.jobs?.title}</h3>
                    <p className="text-gray-600">{match.jobs?.company}</p>
                    <p className="text-sm text-gray-500 mt-1">{match.jobs?.location}</p>
                  </div>
                  <div className="flex items-center ml-4">
                    <TrendingUp className="h-5 w-5 text-green-500 mr-1" />
                    <span className="text-2xl font-bold text-green-600">
                      {Math.round(match.overall_score * 100)}%
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
};
