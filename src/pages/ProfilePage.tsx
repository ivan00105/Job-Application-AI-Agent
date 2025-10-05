/**
 * Profile Page - CV Upload and Management
 */
import { useState, useEffect } from 'react';
import { Layout } from '../components/Layout';
import { cvAPI } from '../api/client';
import { Upload, FileText, CheckCircle, AlertCircle } from 'lucide-react';

export const ProfilePage = () => {
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      const data = await cvAPI.getProfile();
      setProfile(data);
    } catch (err: any) {
      if (err.response?.status !== 404) {
        console.error('Failed to load profile:', err);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setMessage(null);

    try {
      const result = await cvAPI.upload(file);
      setMessage({ type: 'success', text: result.message || 'CV uploaded successfully!' });
      await loadProfile();
    } catch (err: any) {
      setMessage({
        type: 'error',
        text: err.response?.data?.detail || 'Failed to upload CV'
      });
    } finally {
      setUploading(false);
    }
  };

  return (
    <Layout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">My CV Profile</h1>
          <p className="text-gray-600 mt-1">Upload and manage your CV for job matching</p>
        </div>

        {message && (
          <div
            className={`rounded-lg p-4 flex items-start ${
              message.type === 'success'
                ? 'bg-green-50 border border-green-200'
                : 'bg-red-50 border border-red-200'
            }`}
          >
            {message.type === 'success' ? (
              <CheckCircle className="h-5 w-5 text-green-600 mr-3 flex-shrink-0 mt-0.5" />
            ) : (
              <AlertCircle className="h-5 w-5 text-red-600 mr-3 flex-shrink-0 mt-0.5" />
            )}
            <p
              className={message.type === 'success' ? 'text-green-800' : 'text-red-800'}
            >
              {message.text}
            </p>
          </div>
        )}

        <div className="bg-white rounded-lg border p-8">
          <div className="max-w-2xl mx-auto">
            {loading ? (
              <div className="text-center py-8">
                <div className="text-gray-500">Loading...</div>
              </div>
            ) : profile ? (
              <div className="space-y-6">
                <div className="flex items-center justify-between pb-6 border-b">
                  <div className="flex items-center">
                    <FileText className="h-10 w-10 text-blue-600 mr-3" />
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">CV Uploaded</h3>
                      <p className="text-sm text-gray-600">
                        Last updated: {new Date(profile.updated_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <p className="text-blue-800 text-sm">
                    CV parsing with AI will be implemented in the next phase. Currently showing placeholder data.
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Upload New CV
                  </label>
                  <input
                    type="file"
                    accept=".pdf,.docx"
                    onChange={handleFileUpload}
                    disabled={uploading}
                    className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                  />
                </div>
              </div>
            ) : (
              <div className="text-center py-8">
                <Upload className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">Upload Your CV</h3>
                <p className="text-gray-600 mb-6">
                  Upload your resume to get started with AI-powered job matching
                </p>

                <label className="inline-block">
                  <input
                    type="file"
                    accept=".pdf,.docx"
                    onChange={handleFileUpload}
                    disabled={uploading}
                    className="hidden"
                  />
                  <span className="cursor-pointer inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-lg text-white bg-blue-600 hover:bg-blue-700 transition disabled:opacity-50">
                    {uploading ? (
                      'Uploading...'
                    ) : (
                      <>
                        <Upload className="h-5 w-5 mr-2" />
                        Choose File
                      </>
                    )}
                  </span>
                </label>

                <p className="text-xs text-gray-500 mt-3">
                  Supported formats: PDF, DOCX (max 5MB)
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
};
