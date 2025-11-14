/**
 * Profile Page - CV Form with Upload
 */
import { useState, useEffect } from 'react';
import { Layout } from '../components/Layout';
import { cvAPI } from '../api/client';
import { Upload, Save, Plus, Trash2, Loader2 } from 'lucide-react';

interface Experience {
  job_title: string;
  company: string;
  location: string;
  start_date: string;
  end_date: string;
  responsibilities: string[];
}

interface Education {
  degree: string;
  field_of_study: string;
  institution: string;
  location: string;
  graduation_year: string;
  gpa?: string;
}

interface Certification {
  name: string;
  issuer: string;
  date_obtained: string;
  expiry_date?: string;
}

interface Project {
  name: string;
  description: string;
  url?: string;
}

interface CVData {
  personal_info: {
    first_name?: string;
    last_name?: string;
    email?: string;
    phone?: string;
    location?: string;
    linkedin?: string;
    github?: string;
    website?: string;
  };
  professional_summary?: string;
  work_experience: Experience[];
  education: Education[];
  skills: {
    technical: string[];
    soft: string[];
    tools: string[];
  };
  certifications: Certification[];
  languages: Array<{ language: string; proficiency: string }>;
  projects: Project[];
}

const emptyCV: CVData = {
  personal_info: {},
  professional_summary: '',
  work_experience: [],
  education: [],
  skills: { technical: [], soft: [], tools: [] },
  certifications: [],
  languages: [],
  projects: [],
};

export const ProfilePage = () => {
  const [cvData, setCVData] = useState<CVData>(emptyCV);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    loadExistingProfile();
  }, []);

  const loadExistingProfile = async () => {
    try {
      const profile = await cvAPI.getProfile();
      if (profile.parsed_data) {
        setCVData({ ...emptyCV, ...profile.parsed_data });
      }
    } catch (err) {
      console.log('No existing profile');
    } finally {
      setInitialLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setMessage(null);

    try {
      const result = await cvAPI.upload(file);
      setMessage({ type: 'success', text: 'CV parsed successfully!' });
      if (result.parsed_data) {
        setCVData({ ...emptyCV, ...result.parsed_data });
      }
    } catch (err: any) {
      setMessage({
        type: 'error',
        text: err.response?.data?.detail || 'Failed to parse CV',
      });
    } finally {
      setUploading(false);
    }
  };

  const handleSave = async () => {
    setLoading(true);
    setMessage(null);

    try {
      await cvAPI.saveProfile(cvData);
      setMessage({ type: 'success', text: 'CV profile saved successfully!' });
      setTimeout(() => setMessage(null), 5000);
    } catch (err: any) {
      setMessage({
        type: 'error',
        text: err.response?.data?.detail || 'Failed to save CV',
      });
    } finally {
      setLoading(false);
    }
  };

  const addExperience = () => {
    setCVData({
      ...cvData,
      work_experience: [
        ...cvData.work_experience,
        { job_title: '', company: '', location: '', start_date: '', end_date: '', responsibilities: [''] },
      ],
    });
  };

  const addEducation = () => {
    setCVData({
      ...cvData,
      education: [
        ...cvData.education,
        { degree: '', field_of_study: '', institution: '', location: '', graduation_year: '', gpa: '' },
      ],
    });
  };

  const addCertification = () => {
    setCVData({
      ...cvData,
      certifications: [
        ...cvData.certifications,
        { name: '', issuer: '', date_obtained: '', expiry_date: '' },
      ],
    });
  };

  const addProject = () => {
    setCVData({
      ...cvData,
      projects: [
        ...cvData.projects,
        { name: '', description: '', url: '' },
      ],
    });
  };

  const addLanguage = () => {
    setCVData({
      ...cvData,
      languages: [...cvData.languages, { language: '', proficiency: '' }],
    });
  };

  const updateExperience = (index: number, field: string, value: any) => {
    const updated = [...cvData.work_experience];
    updated[index] = { ...updated[index], [field]: value };
    setCVData({ ...cvData, work_experience: updated });
  };

  const updateEducation = (index: number, field: string, value: any) => {
    const updated = [...cvData.education];
    updated[index] = { ...updated[index], [field]: value };
    setCVData({ ...cvData, education: updated });
  };

  const updateCertification = (index: number, field: string, value: any) => {
    const updated = [...cvData.certifications];
    updated[index] = { ...updated[index], [field]: value };
    setCVData({ ...cvData, certifications: updated });
  };

  const updateLanguage = (index: number, field: string, value: any) => {
    const updated = [...cvData.languages];
    updated[index] = { ...updated[index], [field]: value };
    setCVData({ ...cvData, languages: updated });
  };

  const updateProject = (index: number, field: string, value: any) => {
    const updated = [...cvData.projects];
    updated[index] = { ...updated[index], [field]: value };
    setCVData({ ...cvData, projects: updated });
  };

  const removeExperience = (index: number) => {
    setCVData({
      ...cvData,
      work_experience: cvData.work_experience.filter((_, i) => i !== index),
    });
  };

  const removeEducation = (index: number) => {
    setCVData({
      ...cvData,
      education: cvData.education.filter((_, i) => i !== index),
    });
  };

  const removeCertification = (index: number) => {
    setCVData({
      ...cvData,
      certifications: cvData.certifications.filter((_, i) => i !== index),
    });
  };

  const removeLanguage = (index: number) => {
    setCVData({
      ...cvData,
      languages: cvData.languages.filter((_, i) => i !== index),
    });
  };

  const removeProject = (index: number) => {
    setCVData({
      ...cvData,
      projects: cvData.projects.filter((_, i) => i !== index),
    });
  };

  if (initialLoading) {
    return (
      <Layout>
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading profile...</p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-4xl mx-auto p-6">
        <h1 className="text-3xl font-bold mb-6">My CV Profile</h1>

        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Upload CV to Auto-Fill (PDF or DOCX)</h2>
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
            <input
              type="file"
              accept=".pdf,.docx"
              onChange={handleFileUpload}
              className="hidden"
              id="cv-upload"
              disabled={uploading}
            />
            <label htmlFor="cv-upload" className={`cursor-pointer ${uploading ? 'pointer-events-none' : ''}`}>
              {uploading ? (
                <Loader2 className="w-12 h-12 mx-auto mb-4 text-blue-600 animate-spin" />
              ) : (
                <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />
              )}
              <p className={`${uploading ? 'text-blue-600 font-medium' : 'text-gray-600'}`}>
                {uploading ? 'Parsing CV with AI, please wait...' : 'Click to upload PDF or DOCX'}
              </p>
            </label>
          </div>
        </div>

        {message && (
          <div
            className={`mb-6 p-4 rounded ${message.type === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
              }`}
          >
            {message.text}
          </div>
        )}

        <div className="bg-white rounded-lg shadow p-6 space-y-6">
          <div>
            <h2 className="text-xl font-semibold mb-4">Personal Information</h2>
            <div className="grid grid-cols-2 gap-4">
              <input
                type="text"
                placeholder="First Name"
                value={cvData.personal_info.first_name || ''}
                onChange={(e) =>
                  setCVData({
                    ...cvData,
                    personal_info: { ...cvData.personal_info, first_name: e.target.value },
                  })
                }
                className="border rounded px-3 py-2"
              />
              <input
                type="text"
                placeholder="Last Name"
                value={cvData.personal_info.last_name || ''}
                onChange={(e) =>
                  setCVData({
                    ...cvData,
                    personal_info: { ...cvData.personal_info, last_name: e.target.value },
                  })
                }
                className="border rounded px-3 py-2"
              />
              <input
                type="email"
                placeholder="Email"
                value={cvData.personal_info.email || ''}
                onChange={(e) =>
                  setCVData({
                    ...cvData,
                    personal_info: { ...cvData.personal_info, email: e.target.value },
                  })
                }
                className="border rounded px-3 py-2"
              />
              <input
                type="text"
                placeholder="Phone"
                value={cvData.personal_info.phone || ''}
                onChange={(e) =>
                  setCVData({
                    ...cvData,
                    personal_info: { ...cvData.personal_info, phone: e.target.value },
                  })
                }
                className="border rounded px-3 py-2"
              />
              <input
                type="text"
                placeholder="Location"
                value={cvData.personal_info.location || ''}
                onChange={(e) =>
                  setCVData({
                    ...cvData,
                    personal_info: { ...cvData.personal_info, location: e.target.value },
                  })
                }
                className="border rounded px-3 py-2"
              />
              <input
                type="text"
                placeholder="LinkedIn URL"
                value={cvData.personal_info.linkedin || ''}
                onChange={(e) =>
                  setCVData({
                    ...cvData,
                    personal_info: { ...cvData.personal_info, linkedin: e.target.value },
                  })
                }
                className="border rounded px-3 py-2"
              />
              <input
                type="text"
                placeholder="GitHub URL"
                value={cvData.personal_info.github || ''}
                onChange={(e) =>
                  setCVData({
                    ...cvData,
                    personal_info: { ...cvData.personal_info, github: e.target.value },
                  })
                }
                className="border rounded px-3 py-2"
              />
              <input
                type="text"
                placeholder="Website"
                value={cvData.personal_info.website || ''}
                onChange={(e) =>
                  setCVData({
                    ...cvData,
                    personal_info: { ...cvData.personal_info, website: e.target.value },
                  })
                }
                className="border rounded px-3 py-2"
              />
            </div>
          </div>

          <div>
            <h2 className="text-xl font-semibold mb-4">Professional Summary</h2>
            <textarea
              placeholder="Brief professional summary..."
              value={cvData.professional_summary || ''}
              onChange={(e) => setCVData({ ...cvData, professional_summary: e.target.value })}
              className="w-full border rounded px-3 py-2 h-24"
            />
          </div>

          <div>
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">Work Experience</h2>
              <button
                onClick={addExperience}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                <Plus size={20} /> Add Experience
              </button>
            </div>
            {cvData.work_experience.map((exp, index) => (
              <div key={index} className="border rounded p-4 mb-4">
                <div className="flex justify-between mb-2">
                  <h3 className="font-semibold">Experience {index + 1}</h3>
                  <button
                    onClick={() => removeExperience(index)}
                    className="text-red-600 hover:text-red-800"
                  >
                    <Trash2 size={18} />
                  </button>
                </div>
                <div className="grid grid-cols-2 gap-3 mb-3">
                  <input
                    type="text"
                    placeholder="Job Title"
                    value={exp.job_title}
                    onChange={(e) => updateExperience(index, 'job_title', e.target.value)}
                    className="border rounded px-3 py-2"
                  />
                  <input
                    type="text"
                    placeholder="Company"
                    value={exp.company}
                    onChange={(e) => updateExperience(index, 'company', e.target.value)}
                    className="border rounded px-3 py-2"
                  />
                  <input
                    type="text"
                    placeholder="Location"
                    value={exp.location}
                    onChange={(e) => updateExperience(index, 'location', e.target.value)}
                    className="border rounded px-3 py-2"
                  />
                  <input
                    type="text"
                    placeholder="Start Date"
                    value={exp.start_date}
                    onChange={(e) => updateExperience(index, 'start_date', e.target.value)}
                    className="border rounded px-3 py-2"
                  />
                  <input
                    type="text"
                    placeholder="End Date (or Present)"
                    value={exp.end_date}
                    onChange={(e) => updateExperience(index, 'end_date', e.target.value)}
                    className="border rounded px-3 py-2"
                  />
                </div>
                <textarea
                  placeholder="Responsibilities (comma-separated)"
                  value={exp.responsibilities?.join(', ') || ''}
                  onChange={(e) => updateExperience(index, 'responsibilities', e.target.value.split(',').map(r => r.trim()).filter(r => r))}
                  className="w-full border rounded px-3 py-2 h-24"
                />
              </div>
            ))}
          </div>

          <div>
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">Education</h2>
              <button
                onClick={addEducation}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                <Plus size={20} /> Add Education
              </button>
            </div>
            {cvData.education.map((edu, index) => (
              <div key={index} className="border rounded p-4 mb-4">
                <div className="flex justify-between mb-2">
                  <h3 className="font-semibold">Education {index + 1}</h3>
                  <button
                    onClick={() => removeEducation(index)}
                    className="text-red-600 hover:text-red-800"
                  >
                    <Trash2 size={18} />
                  </button>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <input
                    type="text"
                    placeholder="Degree"
                    value={edu.degree}
                    onChange={(e) => updateEducation(index, 'degree', e.target.value)}
                    className="border rounded px-3 py-2"
                  />
                  <input
                    type="text"
                    placeholder="Field of Study"
                    value={edu.field_of_study}
                    onChange={(e) => updateEducation(index, 'field_of_study', e.target.value)}
                    className="border rounded px-3 py-2"
                  />
                  <input
                    type="text"
                    placeholder="Institution"
                    value={edu.institution}
                    onChange={(e) => updateEducation(index, 'institution', e.target.value)}
                    className="border rounded px-3 py-2"
                  />
                  <input
                    type="text"
                    placeholder="Location"
                    value={edu.location}
                    onChange={(e) => updateEducation(index, 'location', e.target.value)}
                    className="border rounded px-3 py-2"
                  />
                  <input
                    type="text"
                    placeholder="Graduation Year"
                    value={edu.graduation_year}
                    onChange={(e) => updateEducation(index, 'graduation_year', e.target.value)}
                    className="border rounded px-3 py-2"
                  />
                  <input
                    type="text"
                    placeholder="GPA (optional)"
                    value={edu.gpa || ''}
                    onChange={(e) => updateEducation(index, 'gpa', e.target.value)}
                    className="border rounded px-3 py-2"
                  />
                </div>
              </div>
            ))}
          </div>

          <div>
            <h2 className="text-xl font-semibold mb-4">Skills</h2>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Technical Skills</label>
                <textarea
                  placeholder="Python&#10;JavaScript&#10;SQL"
                  value={cvData.skills.technical?.join('\n') || ''}
                  onChange={(e) => setCVData({
                    ...cvData,
                    skills: { ...cvData.skills, technical: e.target.value.split('\n') }
                  })}
                  className="w-full border rounded px-3 py-2 h-32 resize-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Soft Skills</label>
                <textarea
                  placeholder="Leadership&#10;Communication&#10;Teamwork"
                  value={cvData.skills.soft?.join('\n') || ''}
                  onChange={(e) => setCVData({
                    ...cvData,
                    skills: { ...cvData.skills, soft: e.target.value.split('\n') }
                  })}
                  className="w-full border rounded px-3 py-2 h-32 resize-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Tools</label>
                <textarea
                  placeholder="Git&#10;Docker&#10;AWS"
                  value={cvData.skills.tools?.join('\n') || ''}
                  onChange={(e) => setCVData({
                    ...cvData,
                    skills: { ...cvData.skills, tools: e.target.value.split('\n') }
                  })}
                  className="w-full border rounded px-3 py-2 h-32 resize-none"
                />
              </div>
            </div>
          </div>

          <div>
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">Certifications</h2>
              <button
                onClick={addCertification}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                <Plus size={20} /> Add Certification
              </button>
            </div>
            {cvData.certifications.map((cert, index) => (
              <div key={index} className="border rounded p-4 mb-4">
                <div className="flex justify-between mb-2">
                  <h3 className="font-semibold">Certification {index + 1}</h3>
                  <button
                    onClick={() => removeCertification(index)}
                    className="text-red-600 hover:text-red-800"
                  >
                    <Trash2 size={18} />
                  </button>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <input
                    type="text"
                    placeholder="Certification Name"
                    value={cert.name}
                    onChange={(e) => updateCertification(index, 'name', e.target.value)}
                    className="border rounded px-3 py-2"
                  />
                  <input
                    type="text"
                    placeholder="Issuer"
                    value={cert.issuer}
                    onChange={(e) => updateCertification(index, 'issuer', e.target.value)}
                    className="border rounded px-3 py-2"
                  />
                  <input
                    type="text"
                    placeholder="Date Obtained (YYYY-MM)"
                    value={cert.date_obtained}
                    onChange={(e) => updateCertification(index, 'date_obtained', e.target.value)}
                    className="border rounded px-3 py-2"
                  />
                  <input
                    type="text"
                    placeholder="Expiry Date (optional)"
                    value={cert.expiry_date || ''}
                    onChange={(e) => updateCertification(index, 'expiry_date', e.target.value)}
                    className="border rounded px-3 py-2"
                  />
                </div>
              </div>
            ))}
          </div>

          <div>
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">Languages</h2>
              <button
                onClick={addLanguage}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                <Plus size={20} /> Add Language
              </button>
            </div>
            {cvData.languages.map((lang, index) => (
              <div key={index} className="border rounded p-4 mb-4">
                <div className="flex justify-between mb-2">
                  <h3 className="font-semibold">Language {index + 1}</h3>
                  <button
                    onClick={() => removeLanguage(index)}
                    className="text-red-600 hover:text-red-800"
                  >
                    <Trash2 size={18} />
                  </button>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <input
                    type="text"
                    placeholder="Language"
                    value={lang.language}
                    onChange={(e) => updateLanguage(index, 'language', e.target.value)}
                    className="border rounded px-3 py-2"
                  />
                  <select
                    value={lang.proficiency}
                    onChange={(e) => updateLanguage(index, 'proficiency', e.target.value)}
                    className="border rounded px-3 py-2"
                  >
                    <option value="">Select Proficiency</option>
                    <option value="Native">Native</option>
                    <option value="Fluent">Fluent</option>
                    <option value="Professional">Professional</option>
                    <option value="Intermediate">Intermediate</option>
                    <option value="Basic">Basic</option>
                  </select>
                </div>
              </div>
            ))}
          </div>

          <div>
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">Projects</h2>
              <button
                onClick={addProject}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                <Plus size={20} /> Add Project
              </button>
            </div>
            {cvData.projects.map((proj, index) => (
              <div key={index} className="border rounded p-4 mb-4">
                <div className="flex justify-between mb-2">
                  <h3 className="font-semibold">Project {index + 1}</h3>
                  <button
                    onClick={() => removeProject(index)}
                    className="text-red-600 hover:text-red-800"
                  >
                    <Trash2 size={18} />
                  </button>
                </div>
                <div className="space-y-3">
                  <input
                    type="text"
                    placeholder="Project Name"
                    value={proj.name}
                    onChange={(e) => updateProject(index, 'name', e.target.value)}
                    className="w-full border rounded px-3 py-2"
                  />
                  <textarea
                    placeholder="Description"
                    value={proj.description}
                    onChange={(e) => updateProject(index, 'description', e.target.value)}
                    className="w-full border rounded px-3 py-2 h-20"
                  />
                  <input
                    type="text"
                    placeholder="Project URL (optional)"
                    value={proj.url || ''}
                    onChange={(e) => updateProject(index, 'url', e.target.value)}
                    className="w-full border rounded px-3 py-2"
                  />
                </div>
              </div>
            ))}
          </div>

          <div className="flex gap-4">
            <button
              onClick={handleSave}
              disabled={loading}
              className="flex items-center gap-2 px-6 py-3 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
            >
              <Save size={20} />
              {loading ? 'Saving...' : 'Save CV Profile'}
            </button>
          </div>
        </div>
      </div>
    </Layout>
  );
};
