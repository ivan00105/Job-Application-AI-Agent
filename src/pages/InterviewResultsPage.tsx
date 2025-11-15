import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Layout } from '../components/Layout';
import { interviewAPI, SessionDetail } from '../api/interviewClient';
import { jobsAPI } from '../api/client';
import { 
  TrendingUp, CheckCircle, Award, ArrowLeft, 
  BarChart3, Target, Clock, FileText, 
  Lightbulb, AlertCircle, Star, TrendingDown,
  ExternalLink, Download, Share2
} from 'lucide-react';

export const InterviewResultsPage = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [sessionDetail, setSessionDetail] = useState<SessionDetail | null>(null);
  const [jobTitle, setJobTitle] = useState<string | null>(null);
  const [loadingJob, setLoadingJob] = useState(false);

  useEffect(() => {
    if (sessionId) {
      loadSessionDetail();
    }
  }, [sessionId]);

  const loadSessionDetail = async () => {
    if (!sessionId) {
      setLoading(false);
      return;
    }
    
    try {
      setLoading(true);
      const detail = await interviewAPI.getSessionDetail(sessionId);
      setSessionDetail(detail);
      
      // Load job title if this is a job-specific interview
      if (detail.session.job_id) {
        setLoadingJob(true);
        try {
          const job = await jobsAPI.getById(detail.session.job_id);
          setJobTitle(job.title || null);
        } catch (err) {
          console.error('Failed to load job:', err);
        } finally {
          setLoadingJob(false);
        }
      }
    } catch (err: any) {
      console.error('Failed to load session detail:', err);
      console.error('Session ID:', sessionId);
      console.error('Error details:', err.response?.data || err.message);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string | undefined) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getScoreColor = (score: number) => {
    if (score >= 4) return 'text-green-600';
    if (score >= 3) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBgColor = (score: number) => {
    if (score >= 4) return 'bg-green-100';
    if (score >= 3) return 'bg-yellow-100';
    return 'bg-red-100';
  };

  const getOverallRating = (score: number) => {
    if (score >= 4.5) return { text: 'Excellent', color: 'text-green-700', bg: 'bg-green-100' };
    if (score >= 4) return { text: 'Very Good', color: 'text-green-600', bg: 'bg-green-50' };
    if (score >= 3.5) return { text: 'Good', color: 'text-blue-600', bg: 'bg-blue-50' };
    if (score >= 3) return { text: 'Fair', color: 'text-yellow-600', bg: 'bg-yellow-50' };
    return { text: 'Needs Improvement', color: 'text-red-600', bg: 'bg-red-50' };
  };

  if (loading) {
    return (
      <Layout>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center py-20">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mb-4"></div>
            <div className="text-gray-600 text-lg">Loading interview results...</div>
          </div>
        </div>
      </Layout>
    );
  }

  if (!sessionDetail) {
    return (
      <Layout>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="bg-red-50 border border-red-200 rounded-lg p-8">
            <div className="flex items-center gap-3 mb-4">
              <AlertCircle className="h-6 w-6 text-red-600" />
              <h2 className="text-xl font-semibold text-red-800">Session not found</h2>
            </div>
            <p className="text-red-700 mb-4">
              The interview session could not be found. It may have been deleted or you may not have permission to view it.
            </p>
            <p className="text-sm text-red-600 mb-6">
              Session ID: {sessionId || 'N/A'}
            </p>
            <button
              onClick={() => navigate('/interviews')}
              className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors flex items-center gap-2"
            >
              <ArrowLeft size={18} />
              Back to Interviews
            </button>
          </div>
        </div>
      </Layout>
    );
  }

  const { session, responses, questions } = sessionDetail;
  const overallPercentage = session.avg_score ? (session.avg_score / 5) * 100 : 0;
  const rating = session.avg_score ? getOverallRating(session.avg_score) : null;

  const getQuestionById = (questionId: string) => {
    return questions.find((q) => q.id === questionId);
  };

  // Calculate category averages
  const categoryScores: Record<string, { total: number; count: number }> = {};
  responses.forEach((response) => {
    const question = getQuestionById(response.question_id);
    const category = question?.category || 'other';
    if (response.evaluation_scores) {
      if (!categoryScores[category]) {
        categoryScores[category] = { total: 0, count: 0 };
      }
      categoryScores[category].total += response.evaluation_scores.overall_score;
      categoryScores[category].count += 1;
    }
  });

  const categoryAverages = Object.entries(categoryScores).map(([category, data]) => ({
    category,
    average: data.total / data.count,
  }));

  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => navigate('/interviews')}
            className="flex items-center text-gray-600 hover:text-gray-900 mb-4 transition-colors"
          >
            <ArrowLeft className="h-5 w-5 mr-2" />
            Back to Interviews
          </button>
          
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-gray-900 mb-2">Interview Results</h1>
              <div className="flex items-center gap-4 text-gray-600">
                <div className="flex items-center gap-2">
                  <Clock size={18} />
                  <span>{formatDate(session.started_at)}</span>
                </div>
                {session.completed_at && (
                  <div className="flex items-center gap-2">
                    <CheckCircle size={18} />
                    <span>Completed: {formatDate(session.completed_at)}</span>
                  </div>
                )}
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => window.print()}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors flex items-center gap-2"
              >
                <Download size={18} />
                Print
              </button>
            </div>
          </div>
        </div>

        {/* Session Info Card */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <div className="text-sm text-gray-500 mb-1">Interview Type</div>
              <div className="text-lg font-semibold text-gray-900">
                {session.domain} Interview
              </div>
              <div className="text-sm text-gray-600 mt-1">
                {session.role_type} Role
              </div>
            </div>
            {jobTitle && (
              <div>
                <div className="text-sm text-gray-500 mb-1">Job Position</div>
                <div className="text-lg font-semibold text-gray-900">
                  {jobTitle}
                </div>
                {session.job_id && (
                  <button
                    onClick={() => navigate(`/applications?tab=saved`)}
                    className="text-sm text-purple-600 hover:text-purple-700 mt-1 flex items-center gap-1"
                  >
                    <ExternalLink size={14} />
                    View Job
                  </button>
                )}
              </div>
            )}
            <div>
              <div className="text-sm text-gray-500 mb-1">Progress</div>
              <div className="text-lg font-semibold text-gray-900">
                {session.completed_questions} / {session.total_questions} Questions
              </div>
              <div className="text-sm text-gray-600 mt-1">
                {((session.completed_questions / session.total_questions) * 100).toFixed(0)}% Complete
              </div>
            </div>
          </div>
        </div>

        {/* Overall Performance Card */}
        <div className="bg-gradient-to-br from-purple-50 via-blue-50 to-indigo-50 border-2 border-purple-200 rounded-xl p-8 mb-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-4">
              <div className="bg-white rounded-full p-4">
                <Award className="h-10 w-10 text-purple-600" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-gray-900">Overall Performance</h2>
                {rating && (
                  <span className={`inline-block mt-2 px-4 py-1 rounded-full text-sm font-semibold ${rating.color} ${rating.bg}`}>
                    {rating.text}
                  </span>
                )}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="bg-white rounded-lg p-6 text-center shadow-sm">
              <div className={`text-5xl font-bold mb-2 ${getScoreColor(session.avg_score || 0)}`}>
                {session.avg_score?.toFixed(1) || 'N/A'}
              </div>
              <div className="text-sm text-gray-600 mb-2">Average Score</div>
              <div className="text-xs text-gray-500">Out of 5.0</div>
            </div>

            <div className="bg-white rounded-lg p-6 text-center shadow-sm">
              <div className="text-5xl font-bold text-blue-600 mb-2">
                {overallPercentage.toFixed(0)}%
              </div>
              <div className="text-sm text-gray-600 mb-2">Overall Percentage</div>
              <div className="text-xs text-gray-500">Performance Rating</div>
            </div>

            <div className="bg-white rounded-lg p-6 text-center shadow-sm">
              <div className="text-5xl font-bold text-green-600 mb-2">
                {session.completed_questions}
              </div>
              <div className="text-sm text-gray-600 mb-2">Questions Answered</div>
              <div className="text-xs text-gray-500">Total: {session.total_questions}</div>
            </div>

            <div className="bg-white rounded-lg p-6 text-center shadow-sm">
              <div className="text-5xl font-bold text-purple-600 mb-2">
                {responses.length}
              </div>
              <div className="text-sm text-gray-600 mb-2">Responses Evaluated</div>
              <div className="text-xs text-gray-500">With Feedback</div>
            </div>
          </div>
        </div>

        {/* Score Breakdown by Category */}
        {categoryAverages.length > 0 && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
            <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <BarChart3 className="text-purple-600" size={24} />
              Performance by Category
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {categoryAverages.map(({ category, average }) => (
                <div key={category} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700 capitalize">
                      {category}
                    </span>
                    <span className={`text-lg font-bold ${getScoreColor(average)}`}>
                      {average.toFixed(1)}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${getScoreBgColor(average)}`}
                      style={{ width: `${(average / 5) * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Detailed Question Breakdown */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-bold text-gray-900 flex items-center gap-2">
              <FileText className="text-purple-600" size={24} />
              Detailed Question Analysis
            </h3>
            <div className="text-sm text-gray-500">
              {responses.length} {responses.length === 1 ? 'Question' : 'Questions'}
            </div>
          </div>

          <div className="space-y-6">
            {responses.map((response, idx) => {
              const question = getQuestionById(response.question_id);
              const scores = response.evaluation_scores;
              const questionScore = scores ? (scores.overall_score / 5) * 100 : 0;

              return (
                <div key={response.id} className="border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
                  {/* Question Header */}
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-3">
                        <div className={`px-3 py-1 rounded-full text-sm font-bold ${getScoreBgColor(scores?.overall_score || 0)} ${getScoreColor(scores?.overall_score || 0)}`}>
                          Question {idx + 1}
                        </div>
                        {question?.category && (
                          <span className="px-3 py-1 bg-gray-100 text-gray-700 text-xs font-medium rounded-full capitalize">
                            {question.category}
                          </span>
                        )}
                        {question?.difficulty && (
                          <span className="px-3 py-1 bg-blue-100 text-blue-700 text-xs font-medium rounded-full capitalize">
                            {question.difficulty}
                          </span>
                        )}
                      </div>
                      <h4 className="text-lg font-semibold text-gray-900 mb-2">
                        {question?.question_text || 'Question not found'}
                      </h4>
                    </div>
                    {scores && (
                      <div className="ml-4 text-right">
                        <div className={`text-3xl font-bold ${getScoreColor(scores.overall_score)}`}>
                          {questionScore.toFixed(0)}%
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                          {scores.overall_score.toFixed(1)}/5.0
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Score Breakdown */}
                  {scores && (
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-4 p-4 bg-gray-50 rounded-lg">
                      <div className="text-center">
                        <div className="text-xs text-gray-600 mb-1">Overall</div>
                        <div className={`text-lg font-bold ${getScoreColor(scores.overall_score)}`}>
                          {scores.overall_score.toFixed(1)}
                        </div>
                      </div>
                      <div className="text-center">
                        <div className="text-xs text-gray-600 mb-1">Relevance</div>
                        <div className={`text-lg font-bold ${getScoreColor(scores.relevance_score)}`}>
                          {scores.relevance_score.toFixed(1)}
                        </div>
                      </div>
                      <div className="text-center">
                        <div className="text-xs text-gray-600 mb-1">Completeness</div>
                        <div className={`text-lg font-bold ${getScoreColor(scores.completeness_score)}`}>
                          {scores.completeness_score.toFixed(1)}
                        </div>
                      </div>
                      <div className="text-center">
                        <div className="text-xs text-gray-600 mb-1">Technical</div>
                        <div className={`text-lg font-bold ${getScoreColor(scores.technical_accuracy_score)}`}>
                          {scores.technical_accuracy_score.toFixed(1)}
                        </div>
                      </div>
                      <div className="text-center">
                        <div className="text-xs text-gray-600 mb-1">Communication</div>
                        <div className={`text-lg font-bold ${getScoreColor(scores.communication_score)}`}>
                          {scores.communication_score.toFixed(1)}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Your Answer */}
                  <div className="mb-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Target className="h-4 w-4 text-gray-500" />
                      <span className="text-sm font-semibold text-gray-700">Your Answer</span>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                      <p className="text-gray-800 whitespace-pre-wrap">{response.user_answer}</p>
                    </div>
                  </div>

                  {/* Feedback */}
                  {response.feedback && (
                    <div className="mb-4">
                      <div className="flex items-center gap-2 mb-2">
                        <Lightbulb className="h-4 w-4 text-blue-500" />
                        <span className="text-sm font-semibold text-gray-700">AI Feedback</span>
                      </div>
                      <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                        <p className="text-gray-700 whitespace-pre-wrap">{response.feedback}</p>
                      </div>
                    </div>
                  )}

                  {/* Strengths and Improvements */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {response.strengths && response.strengths.length > 0 && (
                      <div>
                        <div className="flex items-center gap-2 mb-2">
                          <CheckCircle className="h-4 w-4 text-green-600" />
                          <span className="text-sm font-semibold text-green-700">Strengths</span>
                        </div>
                        <ul className="space-y-2">
                          {response.strengths.map((strength, i) => (
                            <li key={i} className="text-sm text-gray-700 flex items-start gap-2 bg-green-50 p-3 rounded-lg border border-green-200">
                              <Star className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                              <span>{strength}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {response.improvements && response.improvements.length > 0 && (
                      <div>
                        <div className="flex items-center gap-2 mb-2">
                          <TrendingUp className="h-4 w-4 text-orange-600" />
                          <span className="text-sm font-semibold text-orange-700">Areas for Improvement</span>
                        </div>
                        <ul className="space-y-2">
                          {response.improvements.map((improvement, i) => (
                            <li key={i} className="text-sm text-gray-700 flex items-start gap-2 bg-orange-50 p-3 rounded-lg border border-orange-200">
                              <TrendingDown className="h-4 w-4 text-orange-600 mt-0.5 flex-shrink-0" />
                              <span>{improvement}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>

                  {/* Suggested Answer */}
                  {question?.ideal_answer && (
                    <div className="mt-4 pt-4 border-t border-gray-200">
                      <div className="flex items-center gap-2 mb-2">
                        <FileText className="h-4 w-4 text-purple-600" />
                        <span className="text-sm font-semibold text-purple-700">Suggested Answer</span>
                      </div>
                      <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
                        <p className="text-sm text-gray-700 whitespace-pre-wrap">{question.ideal_answer}</p>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-4">
          <button
            onClick={() => navigate('/interviews')}
            className="flex-1 bg-purple-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-purple-700 transition flex items-center justify-center gap-2"
          >
            <ArrowLeft size={20} />
            Back to Interviews
          </button>
          {session.job_id && (
            <button
              onClick={() => navigate(`/interviews?job_id=${session.job_id}`)}
              className="flex-1 bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition flex items-center justify-center gap-2"
            >
              <Target size={20} />
              View All Sessions for This Job
            </button>
          )}
          <button
            onClick={() => navigate('/interview/analytics')}
            className="flex-1 bg-gray-100 text-gray-900 px-6 py-3 rounded-lg font-semibold hover:bg-gray-200 transition flex items-center justify-center gap-2"
          >
            <BarChart3 size={20} />
            View Analytics
          </button>
        </div>
      </div>
    </Layout>
  );
};
