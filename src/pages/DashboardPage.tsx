/**
 * Dashboard Page - Comprehensive landing page with job recommendations, profile analysis, and insights
 */
import { useState, useEffect } from 'react';
import { Layout } from '../components/Layout';
import { ProfileRadarChart } from '../components/RadarChart';
import { DashboardLoader } from '../components/DashboardLoader';
import { matchesAPI, jobsAPI, cvAPI } from '../api/client';
import { 
  Target, 
  TrendingUp, 
  AlertCircle, 
  Upload, 
  Briefcase, 
  Award, 
  Lightbulb,
  ArrowRight,
  Loader2,
  BarChart3
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface ProfileScoring {
  scores: {
    qualification: number;
    experience: number;
    technical_skills: number;
    soft_skills: number;
    tools_platforms: number;
    industry_knowledge: number;
  };
  strengths: string[];
  weaknesses: string[];
  recommendations: Array<{
    dimension: string;
    action: string;
  }>;
  competitor_insights: {
    common_qualifications: string[];
    enhancement_suggestions: string[];
  };
  basic_metrics?: {
    experience_years: number;
    certifications_count: number;
    technical_skills_count: number;
    soft_skills_count: number;
    tools_count: number;
    education_level: string;
  };
}

export const DashboardPage = () => {
  const navigate = useNavigate();
  const [matches, setMatches] = useState<any[]>([]);
  const [recommendedJobs, setRecommendedJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [scoringLoading, setScoringLoading] = useState(false);
  const [error, setError] = useState('');
  const [hasProfile, setHasProfile] = useState(false);
  const [profileScoring, setProfileScoring] = useState<ProfileScoring | null>(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      // Check if profile exists
      try {
        await cvAPI.getProfile();
        setHasProfile(true);
        
        // Load profile scoring
        loadProfileScoring();
        
        // Load recommended jobs
        loadRecommendedJobs();
      } catch (err: any) {
        if (err.response?.status === 404) {
          setHasProfile(false);
        }
      }

      // Load matches
      try {
        const matchesData = await matchesAPI.getMatches(5);
        setMatches(matchesData.matches || []);
      } catch (err: any) {
        if (err.response?.status !== 404) {
          console.error('Failed to load matches:', err);
        }
      }
    } catch (err: any) {
      setError('Failed to load dashboard data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadProfileScoring = async (forceRefresh: boolean = false) => {
    setScoringLoading(true);
    try {
      const scoring = await cvAPI.getProfileScoring(forceRefresh);
      setProfileScoring(scoring);
    } catch (err: any) {
      console.error('Failed to load profile scoring:', err);
      // Don't show error, just don't display scoring
    } finally {
      setScoringLoading(false);
    }
  };

  const handleReanalyze = () => {
    loadProfileScoring(true);
  };

  const loadRecommendedJobs = async () => {
    try {
      const data = await jobsAPI.getRecommended({ limit: 6, hide_saved: false });
      setRecommendedJobs(data.jobs || []);
    } catch (err: any) {
      console.error('Failed to load recommended jobs:', err);
    }
  };

  if (loading) {
    return <DashboardLoader />;
  }

  // Show CV upload prompt if no profile
  if (!hasProfile) {
    return (
      <Layout>
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Welcome to Your Dashboard</h1>
              <p className="text-gray-600 mt-1">Get started by uploading your CV</p>
            </div>
          </div>

          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border-2 border-blue-200 rounded-lg p-8 text-center">
            <Upload className="h-16 w-16 text-blue-600 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Complete Your Profile</h2>
            <p className="text-gray-700 mb-6 max-w-2xl mx-auto">
              Upload your CV to unlock personalized job recommendations, profile analysis, and insights into your strengths and areas for improvement.
            </p>
            <button
              onClick={() => navigate('/profile')}
              className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium"
            >
              <Upload className="h-5 w-5" />
              Upload CV & Complete Profile
              <ArrowRight className="h-5 w-5" />
            </button>
          </div>

          <div className="grid md:grid-cols-3 gap-4 mt-8">
            <div className="bg-white border rounded-lg p-6">
              <Briefcase className="h-8 w-8 text-blue-600 mb-3" />
              <h3 className="font-semibold text-gray-900 mb-2">Job Recommendations</h3>
              <p className="text-sm text-gray-600">
                Get AI-powered job matches based on your skills and experience
              </p>
            </div>
            <div className="bg-white border rounded-lg p-6">
              <BarChart3 className="h-8 w-8 text-green-600 mb-3" />
              <h3 className="font-semibold text-gray-900 mb-2">Profile Analysis</h3>
              <p className="text-sm text-gray-600">
                See your strengths and weaknesses across 6 key dimensions
              </p>
            </div>
            <div className="bg-white border rounded-lg p-6">
              <Award className="h-8 w-8 text-purple-600 mb-3" />
              <h3 className="font-semibold text-gray-900 mb-2">Competitor Insights</h3>
              <p className="text-sm text-gray-600">
                Learn what qualifications competitors have and how to stand out
              </p>
            </div>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      {/* LLM Loading Overlay */}
      {scoringLoading && (
        <div className="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center">
          <div className="bg-white rounded-lg p-8 max-w-md mx-4 shadow-xl">
            <div className="text-center">
              <Loader2 className="h-12 w-12 text-blue-600 animate-spin mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                AI Analysis in Progress
              </h3>
              <p className="text-gray-600 mb-4">
                Our AI is analyzing your profile to generate personalized insights...
              </p>
              <div className="space-y-2 text-sm text-gray-500">
                <p>• Evaluating your qualifications</p>
                <p>• Assessing your experience</p>
                <p>• Analyzing your skills</p>
                <p>• Comparing with market standards</p>
              </div>
              <p className="text-xs text-gray-400 mt-4">
                This may take 30-60 seconds
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
            <p className="text-gray-600 mt-1">Your personalized job search hub</p>
          </div>
        </div>

        {/* Profile Scoring & Radar Chart */}
        {profileScoring && (
          <div className="bg-white border rounded-lg p-6">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-2">
                <BarChart3 className="h-6 w-6 text-blue-600" />
                <h2 className="text-2xl font-bold text-gray-900">Profile Analysis</h2>
                {profileScoring.cached && (
                  <span className="ml-3 px-2 py-1 text-xs bg-green-100 text-green-700 rounded-full">
                    Cached
                  </span>
                )}
              </div>
              <button
                onClick={handleReanalyze}
                disabled={scoringLoading}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
              >
                {scoringLoading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>Analyzing...</span>
                  </>
                ) : (
                  <>
                    <BarChart3 className="h-4 w-4" />
                    <span>Re-analyze Profile</span>
                  </>
                )}
              </button>
            </div>

            {scoringLoading ? (
              <div className="text-center py-12">
                <Loader2 className="h-8 w-8 text-blue-600 animate-spin mx-auto mb-4" />
                <div className="text-gray-500">Analyzing your profile...</div>
              </div>
            ) : (
              <div className="space-y-8">
                {/* Radar Chart and Strengths/Weaknesses Grid */}
                <div className="grid lg:grid-cols-2 gap-8">
                  {/* Radar Chart */}
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Strength & Weakness Analysis</h3>
                    <ProfileRadarChart scores={profileScoring.scores} />
                    <div className="mt-4 text-sm text-gray-600">
                      <p>Scores are based on market standards and competitiveness (0-100 scale)</p>
                    </div>
                  </div>

                  {/* Strengths & Weaknesses */}
                  <div className="space-y-6">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
                        <TrendingUp className="h-5 w-5 text-green-600" />
                        Strengths
                      </h3>
                      <ul className="space-y-2">
                        {profileScoring.strengths && 
                         Array.isArray(profileScoring.strengths) &&
                         profileScoring.strengths.length > 0 ? (
                          profileScoring.strengths.map((strength, idx) => (
                            <li key={idx} className="flex items-start gap-2 text-gray-700">
                              <span className="text-green-600 mt-1">✓</span>
                              <span>{strength}</span>
                            </li>
                          ))
                        ) : (
                          <li className="text-gray-500">No strengths identified yet</li>
                        )}
                      </ul>
                    </div>

                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
                        <AlertCircle className="h-5 w-5 text-yellow-600" />
                        Areas for Improvement
                      </h3>
                      <ul className="space-y-2">
                        {profileScoring.weaknesses && 
                         Array.isArray(profileScoring.weaknesses) &&
                         profileScoring.weaknesses.length > 0 ? (
                          profileScoring.weaknesses.map((weakness, idx) => (
                            <li key={idx} className="flex items-start gap-2 text-gray-700">
                              <span className="text-yellow-600 mt-1">!</span>
                              <span>{weakness}</span>
                            </li>
                          ))
                        ) : (
                          <li className="text-gray-500">No weaknesses identified</li>
                        )}
                      </ul>
                    </div>
                  </div>
                </div>

                {/* Detailed Dimension Analysis - Full Width */}
                <div className="pt-6 border-t border-gray-200">
                  <h4 className="text-lg font-semibold text-gray-900 mb-6">Dimension Breakdown</h4>
                  <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {/* Qualification */}
                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                        <div className="flex items-center gap-2 mb-3">
                          <div className="w-3 h-3 bg-blue-600 rounded-full"></div>
                          <h5 className="font-semibold text-blue-900">Qualification</h5>
                          <span className="ml-auto text-lg font-bold text-blue-700">
                            {Math.round(profileScoring.scores.qualification)}/100
                          </span>
                        </div>
                        <p className="text-sm text-blue-800 mb-3">
                          Evaluates your educational background, degrees, certifications, and academic achievements.
                        </p>
                        
                        {/* How Score is Calculated */}
                        <div className="bg-blue-100/50 rounded p-2 mb-3">
                          <p className="text-xs font-semibold text-blue-900 mb-1">How Your Score is Calculated:</p>
                          <ul className="text-xs text-blue-800 space-y-0.5">
                            <li>• Education level: {profileScoring.basic_metrics?.education_level ? 
                              profileScoring.basic_metrics.education_level.charAt(0).toUpperCase() + profileScoring.basic_metrics.education_level.slice(1) 
                              : 'Not specified'} (weight: 40%)</li>
                            <li>• Certifications: {profileScoring.basic_metrics?.certifications_count || 0} found (weight: 35%)</li>
                            <li>• Degree relevance: Analyzed (weight: 15%)</li>
                            <li>• Academic achievements: Evaluated (weight: 10%)</li>
                          </ul>
                        </div>

                        {/* Improvement Actions */}
                        <div className="bg-white rounded p-2 border border-blue-200">
                          <p className="text-xs font-semibold text-blue-900 mb-1.5">How to Improve:</p>
                          <ul className="text-xs text-blue-800 space-y-1">
                            {profileScoring.scores.qualification >= 80 ? (
                              <>
                                <li className="flex items-start gap-1">
                                  <span className="text-green-600 mt-0.5">✓</span>
                                  <span>Maintain your excellent qualification level</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-blue-600 mt-0.5">→</span>
                                  <span>Consider industry-specific certifications to stay current</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-blue-600 mt-0.5">→</span>
                                  <span>Highlight continuing education and professional development</span>
                                </li>
                              </>
                            ) : profileScoring.scores.qualification >= 60 ? (
                              <>
                                <li className="flex items-start gap-1">
                                  <span className="text-yellow-600 mt-0.5">→</span>
                                  <span>Pursue 2-3 industry-relevant certifications (e.g., AWS, PMP, Google Cloud)</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-yellow-600 mt-0.5">→</span>
                                  <span>Consider online courses or micro-credentials in your field</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-yellow-600 mt-0.5">→</span>
                                  <span>Highlight any academic honors, dean's list, or scholarships</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-yellow-600 mt-0.5">→</span>
                                  <span>Potential impact: +15-20 points</span>
                                </li>
                              </>
                            ) : (
                              <>
                                <li className="flex items-start gap-1">
                                  <span className="text-red-600 mt-0.5">!</span>
                                  <span><strong>Priority:</strong> Obtain relevant professional certifications</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-red-600 mt-0.5">→</span>
                                  <span>Consider pursuing a higher degree if career goals require it</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-red-600 mt-0.5">→</span>
                                  <span>Complete online courses from reputable platforms (Coursera, edX, Udemy)</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-red-600 mt-0.5">→</span>
                                  <span>Join professional associations and attend industry conferences</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-red-600 mt-0.5">→</span>
                                  <span>Potential impact: +25-35 points</span>
                                </li>
                              </>
                            )}
                          </ul>
                        </div>
                      </div>

                      {/* Experience */}
                      <div className="bg-green-50 border border-green-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                        <div className="flex items-center gap-2 mb-3">
                          <div className="w-3 h-3 bg-green-600 rounded-full"></div>
                          <h5 className="font-semibold text-green-900">Experience</h5>
                          <span className="ml-auto text-lg font-bold text-green-700">
                            {Math.round(profileScoring.scores.experience)}/100
                          </span>
                        </div>
                        <p className="text-sm text-green-800 mb-3">
                          Assesses years of relevant work experience, career progression, and role seniority.
                        </p>
                        
                        {/* How Score is Calculated */}
                        <div className="bg-green-100/50 rounded p-2 mb-3">
                          <p className="text-xs font-semibold text-green-900 mb-1">How Your Score is Calculated:</p>
                          <ul className="text-xs text-green-800 space-y-0.5">
                            <li>• Total experience: {profileScoring.basic_metrics?.experience_years || 0} years (weight: 35%)</li>
                            <li>• Career progression: Analyzed (weight: 30%)</li>
                            <li>• Role relevance: Evaluated (weight: 20%)</li>
                            <li>• Leadership roles: Assessed (weight: 15%)</li>
                          </ul>
                        </div>

                        {/* Improvement Actions */}
                        <div className="bg-white rounded p-2 border border-green-200">
                          <p className="text-xs font-semibold text-green-900 mb-1.5">How to Improve:</p>
                          <ul className="text-xs text-green-800 space-y-1">
                            {profileScoring.scores.experience >= 80 ? (
                              <>
                                <li className="flex items-start gap-1">
                                  <span className="text-green-600 mt-0.5">✓</span>
                                  <span>Your experience profile is strong</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-green-600 mt-0.5">→</span>
                                  <span>Continue documenting achievements and impact</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-green-600 mt-0.5">→</span>
                                  <span>Seek leadership opportunities to further enhance profile</span>
                                </li>
                              </>
                            ) : profileScoring.scores.experience >= 60 ? (
                              <>
                                <li className="flex items-start gap-1">
                                  <span className="text-yellow-600 mt-0.5">→</span>
                                  <span>Quantify achievements with metrics (e.g., "Increased sales by 30%")</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-yellow-600 mt-0.5">→</span>
                                  <span>Highlight promotions, expanded responsibilities, and career growth</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-yellow-600 mt-0.5">→</span>
                                  <span>Take on side projects or freelance work to gain relevant experience</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-yellow-600 mt-0.5">→</span>
                                  <span>Potential impact: +10-15 points</span>
                                </li>
                              </>
                            ) : (
                              <>
                                <li className="flex items-start gap-1">
                                  <span className="text-red-600 mt-0.5">!</span>
                                  <span><strong>Priority:</strong> Gain relevant work experience through internships or projects</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-red-600 mt-0.5">→</span>
                                  <span>Volunteer for projects at work that align with target roles</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-red-600 mt-0.5">→</span>
                                  <span>Build portfolio projects demonstrating relevant skills</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-red-600 mt-0.5">→</span>
                                  <span>Emphasize transferable skills from other experiences</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-red-600 mt-0.5">→</span>
                                  <span>Potential impact: +20-30 points</span>
                                </li>
                              </>
                            )}
                          </ul>
                        </div>
                      </div>

                      {/* Technical Skills */}
                      <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                        <div className="flex items-center gap-2 mb-3">
                          <div className="w-3 h-3 bg-purple-600 rounded-full"></div>
                          <h5 className="font-semibold text-purple-900">Technical Skills</h5>
                          <span className="ml-auto text-lg font-bold text-purple-700">
                            {Math.round(profileScoring.scores.technical_skills)}/100
                          </span>
                        </div>
                        <p className="text-sm text-purple-800 mb-3">
                          Measures depth and breadth of technical skills and their relevance to current market demands.
                        </p>
                        
                        {/* How Score is Calculated */}
                        <div className="bg-purple-100/50 rounded p-2 mb-3">
                          <p className="text-xs font-semibold text-purple-900 mb-1">How Your Score is Calculated:</p>
                          <ul className="text-xs text-purple-800 space-y-0.5">
                            <li>• Skills count: {profileScoring.basic_metrics?.technical_skills_count || 0} skills listed (weight: 25%)</li>
                            <li>• Skill depth: Evaluated from experience (weight: 30%)</li>
                            <li>• Market relevance: Compared to job postings (weight: 30%)</li>
                            <li>• Modern technologies: Assessed (weight: 15%)</li>
                          </ul>
                        </div>

                        {/* Improvement Actions */}
                        <div className="bg-white rounded p-2 border border-purple-200">
                          <p className="text-xs font-semibold text-purple-900 mb-1.5">How to Improve:</p>
                          <ul className="text-xs text-purple-800 space-y-1">
                            {profileScoring.scores.technical_skills >= 80 ? (
                              <>
                                <li className="flex items-start gap-1">
                                  <span className="text-green-600 mt-0.5">✓</span>
                                  <span>Strong technical skill foundation</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-purple-600 mt-0.5">→</span>
                                  <span>Stay updated with emerging technologies in your field</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-purple-600 mt-0.5">→</span>
                                  <span>Deepen expertise in core technologies</span>
                                </li>
                              </>
                            ) : profileScoring.scores.technical_skills >= 60 ? (
                              <>
                                <li className="flex items-start gap-1">
                                  <span className="text-yellow-600 mt-0.5">→</span>
                                  <span>Research trending technologies in your industry (check job postings)</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-yellow-600 mt-0.5">→</span>
                                  <span>Complete hands-on projects using new technologies</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-yellow-600 mt-0.5">→</span>
                                  <span>Add 3-5 in-demand skills to your profile</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-yellow-600 mt-0.5">→</span>
                                  <span>Potential impact: +12-18 points</span>
                                </li>
                              </>
                            ) : (
                              <>
                                <li className="flex items-start gap-1">
                                  <span className="text-red-600 mt-0.5">!</span>
                                  <span><strong>Priority:</strong> Build core technical skills through courses and projects</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-red-600 mt-0.5">→</span>
                                  <span>Identify 5-7 essential skills for your target roles</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-red-600 mt-0.5">→</span>
                                  <span>Complete structured learning paths (Udemy, Pluralsight, freeCodeCamp)</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-red-600 mt-0.5">→</span>
                                  <span>Build portfolio projects demonstrating each skill</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-red-600 mt-0.5">→</span>
                                  <span>Potential impact: +25-35 points</span>
                                </li>
                              </>
                            )}
                          </ul>
                        </div>
                      </div>

                      {/* Soft Skills */}
                      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                        <div className="flex items-center gap-2 mb-3">
                          <div className="w-3 h-3 bg-yellow-600 rounded-full"></div>
                          <h5 className="font-semibold text-yellow-900">Soft Skills</h5>
                          <span className="ml-auto text-lg font-bold text-yellow-700">
                            {Math.round(profileScoring.scores.soft_skills)}/100
                          </span>
                        </div>
                        <p className="text-sm text-yellow-800 mb-3">
                          Evaluates communication abilities, leadership, teamwork, and problem-solving skills.
                        </p>
                        
                        {/* How Score is Calculated */}
                        <div className="bg-yellow-100/50 rounded p-2 mb-3">
                          <p className="text-xs font-semibold text-yellow-900 mb-1">How Your Score is Calculated:</p>
                          <ul className="text-xs text-yellow-800 space-y-0.5">
                            <li>• Skills listed: {profileScoring.basic_metrics?.soft_skills_count || 0} skills (weight: 20%)</li>
                            <li>• Leadership evidence: From work experience (weight: 30%)</li>
                            <li>• Communication examples: Analyzed (weight: 25%)</li>
                            <li>• Teamwork indicators: Evaluated (weight: 25%)</li>
                          </ul>
                        </div>

                        {/* Improvement Actions */}
                        <div className="bg-white rounded p-2 border border-yellow-200">
                          <p className="text-xs font-semibold text-yellow-900 mb-1.5">How to Improve:</p>
                          <ul className="text-xs text-yellow-800 space-y-1">
                            {profileScoring.scores.soft_skills >= 80 ? (
                              <>
                                <li className="flex items-start gap-1">
                                  <span className="text-green-600 mt-0.5">✓</span>
                                  <span>Excellent soft skills profile</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-yellow-600 mt-0.5">→</span>
                                  <span>Continue seeking leadership opportunities</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-yellow-600 mt-0.5">→</span>
                                  <span>Mentor others to demonstrate leadership</span>
                                </li>
                              </>
                            ) : profileScoring.scores.soft_skills >= 60 ? (
                              <>
                                <li className="flex items-start gap-1">
                                  <span className="text-yellow-600 mt-0.5">→</span>
                                  <span>Add specific examples of leadership and teamwork in your CV</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-yellow-600 mt-0.5">→</span>
                                  <span>Volunteer for cross-functional projects or team lead roles</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-yellow-600 mt-0.5">→</span>
                                  <span>Take communication courses (Toastmasters, public speaking)</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-yellow-600 mt-0.5">→</span>
                                  <span>Potential impact: +10-15 points</span>
                                </li>
                              </>
                            ) : (
                              <>
                                <li className="flex items-start gap-1">
                                  <span className="text-red-600 mt-0.5">!</span>
                                  <span><strong>Priority:</strong> Develop and demonstrate soft skills</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-red-600 mt-0.5">→</span>
                                  <span>Join Toastmasters or public speaking groups</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-red-600 mt-0.5">→</span>
                                  <span>Volunteer for leadership roles in community or professional groups</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-red-600 mt-0.5">→</span>
                                  <span>Take online courses on leadership and communication</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-red-600 mt-0.5">→</span>
                                  <span>Document teamwork examples with measurable outcomes</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-red-600 mt-0.5">→</span>
                                  <span>Potential impact: +20-30 points</span>
                                </li>
                              </>
                            )}
                          </ul>
                        </div>
                      </div>

                      {/* Tools & Platforms */}
                      <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                        <div className="flex items-center gap-2 mb-3">
                          <div className="w-3 h-3 bg-indigo-600 rounded-full"></div>
                          <h5 className="font-semibold text-indigo-900">Tools & Platforms</h5>
                          <span className="ml-auto text-lg font-bold text-indigo-700">
                            {Math.round(profileScoring.scores.tools_platforms)}/100
                          </span>
                        </div>
                        <p className="text-sm text-indigo-800 mb-3">
                          Assesses familiarity with industry-standard tools, platforms, and technologies.
                        </p>
                        
                        {/* How Score is Calculated */}
                        <div className="bg-indigo-100/50 rounded p-2 mb-3">
                          <p className="text-xs font-semibold text-indigo-900 mb-1">How Your Score is Calculated:</p>
                          <ul className="text-xs text-indigo-800 space-y-0.5">
                            <li>• Tools listed: {profileScoring.basic_metrics?.tools_count || 0} tools/platforms (weight: 30%)</li>
                            <li>• Industry standards: Compared to market (weight: 35%)</li>
                            <li>• Cloud platforms: Assessed (weight: 20%)</li>
                            <li>• Collaboration tools: Evaluated (weight: 15%)</li>
                          </ul>
                        </div>

                        {/* Improvement Actions */}
                        <div className="bg-white rounded p-2 border border-indigo-200">
                          <p className="text-xs font-semibold text-indigo-900 mb-1.5">How to Improve:</p>
                          <ul className="text-xs text-indigo-800 space-y-1">
                            {profileScoring.scores.tools_platforms >= 80 ? (
                              <>
                                <li className="flex items-start gap-1">
                                  <span className="text-green-600 mt-0.5">✓</span>
                                  <span>Strong tool and platform proficiency</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-indigo-600 mt-0.5">→</span>
                                  <span>Stay current with new tool releases and updates</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-indigo-600 mt-0.5">→</span>
                                  <span>Explore advanced features of tools you already know</span>
                                </li>
                              </>
                            ) : profileScoring.scores.tools_platforms >= 60 ? (
                              <>
                                <li className="flex items-start gap-1">
                                  <span className="text-yellow-600 mt-0.5">→</span>
                                  <span>Research essential tools used in your target roles</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-yellow-600 mt-0.5">→</span>
                                  <span>Learn cloud platforms (AWS, Azure, GCP) if relevant</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-yellow-600 mt-0.5">→</span>
                                  <span>Master collaboration tools (Jira, Slack, Confluence, GitHub)</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-yellow-600 mt-0.5">→</span>
                                  <span>Add 5-7 industry-standard tools to your profile</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-yellow-600 mt-0.5">→</span>
                                  <span>Potential impact: +12-18 points</span>
                                </li>
                              </>
                            ) : (
                              <>
                                <li className="flex items-start gap-1">
                                  <span className="text-red-600 mt-0.5">!</span>
                                  <span><strong>Priority:</strong> Learn essential industry tools</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-red-600 mt-0.5">→</span>
                                  <span>Identify top 10 tools from job postings in your field</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-red-600 mt-0.5">→</span>
                                  <span>Use free tiers to practice (AWS Free Tier, GitHub, etc.)</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-red-600 mt-0.5">→</span>
                                  <span>Complete tool-specific tutorials and certifications</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-red-600 mt-0.5">→</span>
                                  <span>Build projects using these tools to demonstrate proficiency</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-red-600 mt-0.5">→</span>
                                  <span>Potential impact: +25-35 points</span>
                                </li>
                              </>
                            )}
                          </ul>
                        </div>
                      </div>

                      {/* Industry Knowledge */}
                      <div className="bg-pink-50 border border-pink-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                        <div className="flex items-center gap-2 mb-3">
                          <div className="w-3 h-3 bg-pink-600 rounded-full"></div>
                          <h5 className="font-semibold text-pink-900">Industry Knowledge</h5>
                          <span className="ml-auto text-lg font-bold text-pink-700">
                            {Math.round(profileScoring.scores.industry_knowledge)}/100
                          </span>
                        </div>
                        <p className="text-sm text-pink-800 mb-3">
                          Measures domain expertise, industry-specific knowledge, and market understanding.
                        </p>
                        
                        {/* How Score is Calculated */}
                        <div className="bg-pink-100/50 rounded p-2 mb-3">
                          <p className="text-xs font-semibold text-pink-900 mb-1">How Your Score is Calculated:</p>
                          <ul className="text-xs text-pink-800 space-y-0.5">
                            <li>• Domain expertise: From experience (weight: 40%)</li>
                            <li>• Industry terminology: Analyzed (weight: 25%)</li>
                            <li>• Market trends: Evaluated (weight: 20%)</li>
                            <li>• Regulatory knowledge: Assessed (weight: 15%)</li>
                          </ul>
                        </div>

                        {/* Improvement Actions */}
                        <div className="bg-white rounded p-2 border border-pink-200">
                          <p className="text-xs font-semibold text-pink-900 mb-1.5">How to Improve:</p>
                          <ul className="text-xs text-pink-800 space-y-1">
                            {profileScoring.scores.industry_knowledge >= 80 ? (
                              <>
                                <li className="flex items-start gap-1">
                                  <span className="text-green-600 mt-0.5">✓</span>
                                  <span>Strong industry knowledge base</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-pink-600 mt-0.5">→</span>
                                  <span>Stay current with industry publications and news</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-pink-600 mt-0.5">→</span>
                                  <span>Share knowledge through articles or presentations</span>
                                </li>
                              </>
                            ) : profileScoring.scores.industry_knowledge >= 60 ? (
                              <>
                                <li className="flex items-start gap-1">
                                  <span className="text-yellow-600 mt-0.5">→</span>
                                  <span>Follow industry leaders on LinkedIn and Twitter</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-yellow-600 mt-0.5">→</span>
                                  <span>Read industry publications and research reports regularly</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-yellow-600 mt-0.5">→</span>
                                  <span>Attend webinars, conferences, and networking events</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-yellow-600 mt-0.5">→</span>
                                  <span>Join industry-specific professional associations</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-yellow-600 mt-0.5">→</span>
                                  <span>Potential impact: +10-15 points</span>
                                </li>
                              </>
                            ) : (
                              <>
                                <li className="flex items-start gap-1">
                                  <span className="text-red-600 mt-0.5">!</span>
                                  <span><strong>Priority:</strong> Build industry knowledge systematically</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-red-600 mt-0.5">→</span>
                                  <span>Subscribe to industry newsletters and publications</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-red-600 mt-0.5">→</span>
                                  <span>Take industry-specific courses or certifications</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-red-600 mt-0.5">→</span>
                                  <span>Join professional associations and attend events</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-red-600 mt-0.5">→</span>
                                  <span>Network with industry professionals on LinkedIn</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-red-600 mt-0.5">→</span>
                                  <span>Research top companies and their business models</span>
                                </li>
                                <li className="flex items-start gap-1">
                                  <span className="text-red-600 mt-0.5">→</span>
                                  <span>Potential impact: +20-30 points</span>
                                </li>
                              </>
                            )}
                          </ul>
                        </div>
                      </div>
                    </div>
                  </div>
              </div>
            )}
          </div>
        )}

        {/* Recommended Jobs */}
        <div className="bg-white border rounded-lg p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-2">
              <Briefcase className="h-6 w-6 text-blue-600" />
              <h2 className="text-2xl font-bold text-gray-900">New Jobs You May Be Interested In</h2>
            </div>
            <button
              onClick={() => navigate('/jobs')}
              className="text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1"
            >
              View All
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>

          {recommendedJobs.length > 0 ? (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {recommendedJobs.slice(0, 6).map((job: any) => (
                <div
                  key={job.id}
                  className="border rounded-lg p-4 hover:shadow-md transition cursor-pointer"
                  onClick={() => navigate(`/jobs`)}
                >
                  <h3 className="font-semibold text-gray-900 mb-1">{job.title}</h3>
                  <p className="text-sm text-gray-600 mb-2">{job.company}</p>
                  <p className="text-xs text-gray-500">{job.location}</p>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <Briefcase className="h-12 w-12 text-gray-400 mx-auto mb-3" />
              <p>No recommended jobs at the moment. Check back later!</p>
            </div>
          )}
        </div>

        {/* Competitor Analysis & Recommendations */}
        {profileScoring?.competitor_insights && (
          <div className="bg-white border rounded-lg p-6">
            <div className="flex items-center gap-2 mb-6">
              <Award className="h-6 w-6 text-purple-600" />
              <h2 className="text-2xl font-bold text-gray-900">Competitor Insights & Recommendations</h2>
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              {/* Common Qualifications */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Common Qualifications by Competitors</h3>
                {profileScoring.competitor_insights?.common_qualifications && 
                 Array.isArray(profileScoring.competitor_insights.common_qualifications) &&
                 profileScoring.competitor_insights.common_qualifications.length > 0 ? (
                  <ul className="space-y-2">
                    {profileScoring.competitor_insights.common_qualifications.map((qual, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-gray-700">
                        <span className="text-purple-600 mt-1">•</span>
                        <span>{qual}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-gray-500">No competitor data available</p>
                )}
              </div>

              {/* Enhancement Suggestions */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
                  <Lightbulb className="h-5 w-5 text-yellow-600" />
                  How to Enhance Your Experience
                </h3>
                {profileScoring.competitor_insights?.enhancement_suggestions && 
                 Array.isArray(profileScoring.competitor_insights.enhancement_suggestions) &&
                 profileScoring.competitor_insights.enhancement_suggestions.length > 0 ? (
                  <ul className="space-y-2">
                    {profileScoring.competitor_insights.enhancement_suggestions.map((suggestion, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-gray-700">
                        <span className="text-yellow-600 mt-1">→</span>
                        <span>{suggestion}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-gray-500">No suggestions available</p>
                )}
              </div>
            </div>

            {/* Recommendations by Dimension */}
            {profileScoring.recommendations && profileScoring.recommendations.length > 0 && (
              <div className="mt-6 pt-6 border-t">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Targeted Recommendations</h3>
                <div className="grid md:grid-cols-2 gap-4">
                  {profileScoring.recommendations.map((rec, idx) => (
                    <div key={idx} className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <div className="font-medium text-blue-900 mb-1 capitalize">
                        {rec.dimension.replace('_', ' ')}
                      </div>
                      <div className="text-sm text-blue-800">{rec.action}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Top Matches */}
        {matches.length > 0 && (
          <div className="bg-white border rounded-lg p-6">
            <div className="flex items-center gap-2 mb-6">
              <Target className="h-6 w-6 text-green-600" />
              <h2 className="text-2xl font-bold text-gray-900">Top Job Matches</h2>
            </div>
            <div className="grid gap-4">
              {matches.map((match: any) => (
                <div
                  key={match.id}
                  className="border rounded-lg p-4 hover:shadow-md transition cursor-pointer"
                  onClick={() => navigate('/jobs')}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-gray-900">{match.jobs?.title}</h3>
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
          </div>
        )}

        {/* Update Profile CTA */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-blue-900 mb-1">Keep Your Profile Updated</h3>
              <p className="text-blue-700 text-sm">
                Update your CV to get the most accurate recommendations and insights
              </p>
            </div>
            <button
              onClick={() => navigate('/profile')}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium"
            >
              Update Profile
            </button>
          </div>
        </div>
      </div>
    </Layout>
  );
};
