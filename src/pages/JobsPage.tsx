/**
 * Jobs Page - Browse all jobs
 */
import { useState, useEffect } from 'react';
import { Layout } from '../components/Layout';
import { jobsAPI } from '../api/client';
import { Search, MapPin, DollarSign } from 'lucide-react';

export const JobsPage = () => {
  const [jobs, setJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadJobs();
  }, []);

  const loadJobs = async () => {
    try {
      const data = await jobsAPI.search({ limit: 50 });
      setJobs(data.jobs || []);
    } catch (err) {
      console.error('Failed to load jobs:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const data = await jobsAPI.search({ query: searchQuery, limit: 50 });
      setJobs(data.jobs || []);
    } catch (err) {
      console.error('Search failed:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Browse Jobs</h1>
          <p className="text-gray-600 mt-1">Search and explore available positions</p>
        </div>

        <form onSubmit={handleSearch} className="flex gap-2">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search jobs by title, company, or keywords..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <button
            type="submit"
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            Search
          </button>
        </form>

        {loading ? (
          <div className="text-center py-12">
            <div className="text-gray-500">Loading jobs...</div>
          </div>
        ) : jobs.length === 0 ? (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-12 text-center">
            <p className="text-gray-600">
              No jobs found. Job scraping will be implemented in later phases.
            </p>
          </div>
        ) : (
          <div className="grid gap-4">
            {jobs.map((job: any) => (
              <div key={job.id} className="bg-white border rounded-lg p-6 hover:shadow-md transition">
                <h3 className="text-xl font-semibold text-gray-900">{job.title}</h3>
                <p className="text-gray-700 font-medium mt-1">{job.company}</p>

                <div className="flex items-center gap-4 mt-3 text-sm text-gray-600">
                  {job.location && (
                    <span className="flex items-center">
                      <MapPin className="h-4 w-4 mr-1" />
                      {job.location}
                    </span>
                  )}
                  {job.salary_min && (
                    <span className="flex items-center">
                      <DollarSign className="h-4 w-4 mr-1" />
                      {job.salary_min.toLocaleString()}
                      {job.salary_max && ` - ${job.salary_max.toLocaleString()}`}
                    </span>
                  )}
                </div>

                {job.description && (
                  <p className="text-gray-600 mt-3 line-clamp-2">{job.description}</p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
};
