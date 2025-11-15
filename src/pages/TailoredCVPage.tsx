import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Layout } from '../components/Layout';
import { FileText, Download, ArrowLeft, Loader2 } from 'lucide-react';
import api from '../api/client';

export const TailoredCVPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [cvData, setCvData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      loadTailoredCV(id);
    }
  }, [id]);

  const loadTailoredCV = async (cvId: string) => {
    try {
      setLoading(true);
      const response = await api.get(`/applications/prepare/cv/${cvId}`);
      setCvData(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load tailored CV');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/applications')}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Tailored CV</h1>
            <p className="text-gray-600 mt-1">Your customized resume for this job</p>
          </div>
        </div>

        {loading ? (
          <div className="text-center py-12">
            <Loader2 className="h-12 w-12 animate-spin mx-auto text-blue-600" />
            <p className="mt-4 text-gray-600">Loading tailored CV...</p>
          </div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <p className="text-red-800">{error}</p>
          </div>
        ) : cvData ? (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
            <div className="flex justify-between items-center mb-6">
              <div>
                <h2 className="text-2xl font-bold text-gray-900">{cvData.job_title}</h2>
                <p className="text-gray-600">{cvData.company}</p>
              </div>
              <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                <Download className="h-4 w-4" />
                Download PDF
              </button>
            </div>
            
            {cvData.emphasis_notes && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                <h3 className="font-semibold text-blue-900 mb-2">What Was Emphasized:</h3>
                <p className="text-blue-800 text-sm">{cvData.emphasis_notes}</p>
              </div>
            )}
            
            <div className="prose max-w-none">
              {cvData.tailored_content && (
                <>
                  {cvData.tailored_content.tailored_summary && (
                    <div className="mb-6">
                      <h3 className="text-xl font-bold text-gray-900 mb-2">Professional Summary</h3>
                      <p className="text-gray-700 leading-relaxed">{cvData.tailored_content.tailored_summary}</p>
                    </div>
                  )}
                  
                  {cvData.tailored_content.highlighted_skills && cvData.tailored_content.highlighted_skills.length > 0 && (
                    <div className="mb-6">
                      <h3 className="text-xl font-bold text-gray-900 mb-3">Key Skills</h3>
                      <div className="flex flex-wrap gap-2">
                        {cvData.tailored_content.highlighted_skills.map((skill: any, idx: number) => (
                          <div key={idx} className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium">
                            {typeof skill === 'string' ? skill : skill.skill || skill}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {cvData.tailored_content.reordered_experience && cvData.tailored_content.reordered_experience.length > 0 && (
                    <div className="mb-6">
                      <h3 className="text-xl font-bold text-gray-900 mb-3">Work Experience</h3>
                      <div className="space-y-4">
                        {cvData.tailored_content.reordered_experience.map((exp: any, idx: number) => (
                          <div key={idx} className="border-l-4 border-blue-500 pl-4">
                            <h4 className="font-semibold text-gray-900">{exp.job_title || exp.title}</h4>
                            <p className="text-gray-600">{exp.company}</p>
                            {exp.emphasis_notes && (
                              <p className="text-sm text-blue-600 mt-1 italic">{exp.emphasis_notes}</p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {!cvData.tailored_content.tailored_summary && 
                   !cvData.tailored_content.highlighted_skills && 
                   !cvData.tailored_content.reordered_experience && (
                    <div className="bg-gray-50 rounded-lg p-4">
                      <p className="text-gray-600">CV content is being processed. Please check back later.</p>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        ) : null}
      </div>
    </Layout>
  );
};

