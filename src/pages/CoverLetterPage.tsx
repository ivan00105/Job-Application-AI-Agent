import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Layout } from '../components/Layout';
import { Mail, Download, ArrowLeft, Loader2, Edit } from 'lucide-react';
import api from '../api/client';

export const CoverLetterPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [coverLetter, setCoverLetter] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState('');

  useEffect(() => {
    if (id) {
      loadCoverLetter(id);
    }
  }, [id]);

  const loadCoverLetter = async (letterId: string) => {
    try {
      setLoading(true);
      const response = await api.get(`/applications/prepare/cover-letter/${letterId}`);
      setCoverLetter(response.data);
      setEditedContent(response.data.content);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load cover letter');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      const response = await api.put(`/applications/prepare/cover-letter/${id}`, {
        content: editedContent
      });
      setCoverLetter(response.data);
      setIsEditing(false);
      alert('Cover letter saved successfully!');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to save cover letter');
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
            <h1 className="text-3xl font-bold text-gray-900">Cover Letter</h1>
            <p className="text-gray-600 mt-1">Your personalized cover letter for this job</p>
          </div>
        </div>

        {loading ? (
          <div className="text-center py-12">
            <Loader2 className="h-12 w-12 animate-spin mx-auto text-blue-600" />
            <p className="mt-4 text-gray-600">Loading cover letter...</p>
          </div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <p className="text-red-800">{error}</p>
          </div>
        ) : coverLetter ? (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
            <div className="flex justify-between items-center mb-6">
              <div>
                <h2 className="text-2xl font-bold text-gray-900">{coverLetter.job_title}</h2>
                <p className="text-gray-600">{coverLetter.company}</p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setIsEditing(!isEditing)}
                  className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
                >
                  <Edit className="h-4 w-4" />
                  {isEditing ? 'Cancel' : 'Edit'}
                </button>
                <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                  <Download className="h-4 w-4" />
                  Download PDF
                </button>
              </div>
            </div>
            {isEditing ? (
              <div className="space-y-4">
                <textarea
                  value={editedContent}
                  onChange={(e) => setEditedContent(e.target.value)}
                  className="w-full h-96 p-4 border border-gray-300 rounded-lg font-mono text-sm"
                />
                <button
                  onClick={handleSave}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Save Changes
                </button>
              </div>
            ) : (
              <div className="prose max-w-none">
                <div className="whitespace-pre-wrap text-gray-700 leading-relaxed">
                  {coverLetter.content}
                </div>
              </div>
            )}
          </div>
        ) : null}
      </div>
    </Layout>
  );
};

