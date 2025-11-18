import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Layout } from '../components/Layout';
import { CVEditor } from '../components/CVEditor';
import { Loader2 } from 'lucide-react';
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
      setError(null);
      const response = await api.get(`/applications/prepare/cv/${cvId}`);
      setCvData(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load tailored CV');
    } finally {
      setLoading(false);
    }
  };

  const handleEditorSave = async (html: string, saveStatus: 'draft' | 'final') => {
    // Reload CV to show updated content
    if (id) {
      await loadTailoredCV(id);
    }
  };

  // Show loading state
  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <Loader2 className="h-12 w-12 animate-spin mx-auto text-blue-600" />
            <p className="mt-4 text-gray-600">Loading tailored CV...</p>
          </div>
      </div>
      </Layout>
    );
  }

  // Show error state
  if (error || !cvData) {
  return (
    <Layout>
        <div className="flex items-center justify-center min-h-screen">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md">
            <p className="text-red-800 mb-4">{error || 'CV not found'}</p>
          <button
            onClick={() => navigate('/applications')}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
          >
              Go Back
          </button>
          </div>
        </div>
      </Layout>
    );
  }

  // Show error if no HTML content
  if (!cvData.html_content) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-screen">
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 max-w-md">
            <p className="text-yellow-800 mb-4">CV content is not available yet. Please regenerate the CV.</p>
                <button 
              onClick={() => navigate('/applications')}
              className="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700"
            >
              Go Back
                </button>
              </div>
            </div>
      </Layout>
    );
  }
            
  // Show editor directly
  return (
    <div className="fixed inset-0 z-50 bg-white">
      <CVEditor
        cvId={id!}
        initialHtml={cvData.html_content}
        jobTitle={cvData.job_title}
        company={cvData.company}
        jobId={cvData.job_id}
        onSave={handleEditorSave}
        onClose={() => navigate('/applications')}
                  />
                </div>
  );
};

