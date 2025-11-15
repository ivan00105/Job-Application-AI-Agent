/**
 * Jobs Page - Browse all jobs with application tracking
 */
import { useState, useEffect } from 'react';
import { Layout } from '../components/Layout';
import { JobCard } from '../components/JobCard';
import { jobsAPI } from '../api/client';
import { Search, MapPin, AlertCircle, X, Loader2, CheckCircle2, Sparkles, Clock } from 'lucide-react';
import { applicationsAPI } from '../api/client';

export const JobsPage = () => {
  const [jobs, setJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true); // Start with loading true to show recommended jobs on load
  const [loadingMore, setLoadingMore] = useState(false);
  const [preparationStatuses, setPreparationStatuses] = useState<Record<string, any>>({});
  const [searchQuery, setSearchQuery] = useState('');
  const [locationQuery, setLocationQuery] = useState('');
  const [hideSaved, setHideSaved] = useState(false);
  const [loadedCount, setLoadedCount] = useState(0);
  const [pageSize] = useState(25);
  const [totalJobs, setTotalJobs] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);
  
  // Active search values (used for display and search execution)
  const [activeSearchQuery, setActiveSearchQuery] = useState('');
  const [activeLocationQuery, setActiveLocationQuery] = useState('');
  
  // Search process tracking
  const [searchSteps, setSearchSteps] = useState<Array<{step: string, status: 'pending' | 'active' | 'completed' | 'skipped', message?: string}>>([]);
  const [searchSource, setSearchSource] = useState<string>('');

  // Load jobs function (called manually or when filters change after initial search)
  const loadJobs = async (reset: boolean = true, searchQueryOverride?: string, locationQueryOverride?: string) => {
    setLoading(true);
    setError(null);
    if (reset) {
      setJobs([]);
      setLoadedCount(0);
      setSearchSteps([]);
      setSearchSource('');
    }
    
    // Use override values if provided, otherwise use active search values
    const queryToUse = searchQueryOverride !== undefined ? searchQueryOverride : activeSearchQuery;
    const locationToUse = locationQueryOverride !== undefined ? locationQueryOverride : activeLocationQuery;
    
    try {
      const offset = reset ? 0 : loadedCount;
      
      // Use vector similarity search if there's a search query
      // Otherwise use simple keyword search
      if (queryToUse.trim()) {
        // Show search steps for vector search
        setSearchSteps([
          { step: 'cv', status: 'active', message: 'Reading CV...' },
          { step: 'saved', status: 'pending', message: 'Reading latest saved jobs...' },
          { step: 'ai', status: 'pending', message: 'AI Analysis...' },
          { step: 'match', status: 'pending', message: 'Job Matching...' }
        ]);
        
        setTimeout(() => {
          setSearchSteps(prev => prev.map(s => s.step === 'cv' ? { ...s, status: 'completed' as const } : s));
          setSearchSteps(prev => prev.map(s => s.step === 'saved' ? { ...s, status: 'active' as const } : s));
        }, 300);
        
        setTimeout(() => {
          setSearchSteps(prev => prev.map(s => s.step === 'saved' ? { ...s, status: 'completed' as const } : s));
          setSearchSteps(prev => prev.map(s => s.step === 'ai' ? { ...s, status: 'active' as const } : s));
        }, 600);
        
        setTimeout(() => {
          setSearchSteps(prev => prev.map(s => s.step === 'ai' ? { ...s, status: 'completed' as const } : s));
          setSearchSteps(prev => prev.map(s => s.step === 'match' ? { ...s, status: 'active' as const } : s));
        }, 900);
        try {
          // Use vector search for semantic similarity
          const data = await jobsAPI.searchVector({
            query: queryToUse.trim(),
            location: locationToUse.trim() || undefined,
            hide_saved: hideSaved,
            limit: pageSize,
            offset: offset,
          });
          if (reset) {
            setJobs(data.jobs || []);
            setLoadedCount(data.jobs?.length || 0);
          } else {
            setJobs(prev => [...prev, ...(data.jobs || [])]);
            setLoadedCount(prev => prev + (data.jobs?.length || 0));
          }
          setTotalJobs(data.total || 0);
          setSearchSteps(prev => prev.map(s => s.step === 'match' ? { ...s, status: 'completed' as const, message: `Found ${data.total || 0} matching jobs` } : s));
          setSearchSource('vector_search');
          
          // Load preparation statuses for saved/applied jobs
          if (reset) {
            loadPreparationStatuses(data.jobs || []);
          }
        } catch (vectorErr: any) {
          // Fallback to keyword search if vector search fails
          console.warn('Vector search failed, falling back to keyword search:', vectorErr);
          setSearchSteps([
            { step: 'cv', status: 'completed', message: 'Reading CV...' },
            { step: 'saved', status: 'completed', message: 'Reading latest saved jobs...' },
            { step: 'ai', status: 'completed', message: 'AI Analysis...' },
            { step: 'match', status: 'active', message: 'Job Matching...' }
          ]);
          const searchParams: any = {
            query: queryToUse.trim(),
            limit: pageSize,
            offset: offset,
            hide_saved: hideSaved
          };
          
          if (locationToUse.trim()) {
            searchParams.location = locationToUse.trim();
          }

          const data = await jobsAPI.search(searchParams);
          if (reset) {
            setJobs(data.jobs || []);
            setLoadedCount(data.jobs?.length || 0);
          } else {
            setJobs(prev => [...prev, ...(data.jobs || [])]);
            setLoadedCount(prev => prev + (data.jobs?.length || 0));
          }
          setTotalJobs(data.total || 0);
          setSearchSteps(prev => prev.map(s => s.step === 'match' ? { ...s, status: 'completed' as const, message: `Found ${data.total || 0} jobs` } : s));
          setSearchSource('keyword_search');
          
          // Load preparation statuses for saved/applied jobs
          if (reset) {
            loadPreparationStatuses(data.jobs || []);
          }
        }
      } else {
        // No search query - get recommended jobs (based on CV, saved jobs, or latest)
        // Show matching steps
        setSearchSteps([
          { step: 'cv', status: 'active', message: 'Reading CV...' },
          { step: 'saved', status: 'pending', message: 'Reading latest saved jobs...' },
          { step: 'ai', status: 'pending', message: 'AI Analysis...' },
          { step: 'match', status: 'pending', message: 'Job Matching...' }
        ]);
        
        try {
          const data = await jobsAPI.getRecommended({
            limit: pageSize,
            offset: offset,
            hide_saved: hideSaved
          });
          if (reset) {
            setJobs(data.jobs || []);
            setLoadedCount(data.jobs?.length || 0);
          } else {
            setJobs(prev => [...prev, ...(data.jobs || [])]);
            setLoadedCount(prev => prev + (data.jobs?.length || 0));
          }
          setTotalJobs(data.total || 0);
          
          // Update steps based on source
          const source = data.source || 'latest';
          setSearchSource(source);
          
          if (source === 'cv_matches' || source === 'cv_vector_search') {
            setSearchSteps([
              { step: 'cv', status: 'completed', message: 'CV profile found' },
              { step: 'saved', status: 'skipped', message: 'Using CV matches' },
              { step: 'ai', status: 'completed', message: 'AI Analysis completed' },
              { step: 'match', status: 'completed', message: `Found ${data.total || 0} jobs matching your CV` }
            ]);
          } else if (source === 'similar_to_saved') {
            setSearchSteps([
              { step: 'cv', status: 'skipped', message: 'No CV profile' },
              { step: 'saved', status: 'completed', message: 'Found saved jobs' },
              { step: 'ai', status: 'completed', message: 'AI Analysis completed' },
              { step: 'match', status: 'completed', message: `Found ${data.total || 0} similar jobs` }
            ]);
          } else {
            setSearchSteps([
              { step: 'cv', status: 'skipped', message: 'No CV profile' },
              { step: 'saved', status: 'skipped', message: 'No saved jobs' },
              { step: 'ai', status: 'skipped', message: 'Using latest jobs' },
              { step: 'match', status: 'completed', message: `Showing ${data.total || 0} latest jobs` }
            ]);
          }
        } catch (err: any) {
          // Fallback to simple keyword search if recommended fails
          console.warn('Recommended jobs failed, using simple search:', err);
          setSearchSteps([
            { step: 'cv', status: 'completed', message: 'Reading CV...' },
            { step: 'saved', status: 'completed', message: 'Reading latest saved jobs...' },
            { step: 'ai', status: 'completed', message: 'AI Analysis...' },
            { step: 'match', status: 'active', message: 'Job Matching...' }
          ]);
          const searchParams: any = {
            limit: pageSize,
            offset: offset,
            hide_saved: hideSaved
          };
          
          if (activeLocationQuery.trim()) {
            searchParams.location = activeLocationQuery.trim();
          }

          const data = await jobsAPI.search(searchParams);
          if (reset) {
            setJobs(data.jobs || []);
            setLoadedCount(data.jobs?.length || 0);
          } else {
            setJobs(prev => [...prev, ...(data.jobs || [])]);
            setLoadedCount(prev => prev + (data.jobs?.length || 0));
          }
          setTotalJobs(data.total || 0);
          setSearchSteps(prev => prev.map(s => ({ ...s, status: 'completed' as const })));
          setSearchSource('fallback');
          
          // Load preparation statuses for saved/applied jobs
          if (reset) {
            loadPreparationStatuses(data.jobs || []);
          }
        }
      }
    } catch (err: any) {
      console.error('Failed to load jobs:', err);
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to load jobs. Please try again.';
      setError(errorMessage);
      setSearchSteps(prev => prev.map(s => ({ ...s, status: 'pending' as const })));
      if (reset) {
        setJobs([]);
        setTotalJobs(0);
        setLoadedCount(0);
      }
    } finally {
      setLoading(false);
    }
  };

  // Load recommended jobs on initial page load
  useEffect(() => {
    if (!hasSearched) {
      // Auto-load recommended jobs when page first loads
      loadJobs(true);
      setHasSearched(true); // Mark as searched so filter changes will trigger reloads
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Reload jobs when hideSaved filter changes (only if user has already searched)
  useEffect(() => {
    if (hasSearched) {
      loadJobs(true);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hideSaved]);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    // Update active search values from current input values
    setActiveSearchQuery(searchQuery);
    setActiveLocationQuery(locationQuery);
    setHasSearched(true);
    // Pass search values directly to loadJobs to avoid async state issues
    await loadJobs(true, searchQuery, locationQuery);
  };

  const handleClearSearch = () => {
    setSearchQuery('');
    setLocationQuery('');
    setActiveSearchQuery('');
    setActiveLocationQuery('');
    setJobs([]);
    setTotalJobs(0);
    setLoadedCount(0);
    setHasSearched(false);
    setError(null);
    // Reload recommended jobs after clearing
    loadJobs(true);
  };

  const handleLoadMore = async () => {
    if (loadingMore || loadedCount >= totalJobs || !hasSearched) return;
    
    setLoadingMore(true);
    setError(null);
    
    try {
      const offset = loadedCount;
      
      // Use the same logic as loadJobs but for loading more
      if (activeSearchQuery.trim()) {
        // Has search query - use search
        await loadJobs(false);
      } else {
        // No search query - get more recommended jobs
        try {
          const data = await jobsAPI.getRecommended({
            limit: pageSize,
            offset: offset,
            hide_saved: hideSaved
          });
          setJobs(prev => [...prev, ...(data.jobs || [])]);
          setLoadedCount(prev => prev + (data.jobs?.length || 0));
          setTotalJobs(data.total || 0);
        } catch (err: any) {
          // Fallback to simple search
          const searchParams: any = {
            limit: pageSize,
            offset: offset,
            hide_saved: hideSaved
          };
          
          if (activeLocationQuery.trim()) {
            searchParams.location = activeLocationQuery.trim();
          }

          const data = await jobsAPI.search(searchParams);
          setJobs(prev => [...prev, ...(data.jobs || [])]);
          setLoadedCount(prev => prev + (data.jobs?.length || 0));
          setTotalJobs(data.total || 0);
        }
      }
    } catch (err: any) {
      console.error('Failed to load more jobs:', err);
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to load more jobs. Please try again.';
      setError(errorMessage);
    } finally {
      setLoadingMore(false);
    }
  };

  const handleApplicationUpdate = () => {
    // Reload all loaded jobs after application status change
    const reloadJobs = async () => {
      setLoading(true);
      setError(null);
      try {
        // Reload all currently loaded jobs
        const searchParams: any = {
          limit: loadedCount || pageSize,
          offset: 0,
          hide_saved: hideSaved
        };
        
        if (activeSearchQuery.trim()) {
          searchParams.query = activeSearchQuery.trim();
        }
        
        if (activeLocationQuery.trim()) {
          searchParams.location = activeLocationQuery.trim();
        }

        const data = await jobsAPI.search(searchParams);
        setJobs(data.jobs || []);
        setTotalJobs(data.total || 0);
        setLoadedCount(data.jobs?.length || 0);
      } catch (err: any) {
        console.error('Failed to reload jobs:', err);
        const errorMessage = err.response?.data?.detail || err.message || 'Failed to reload jobs. Please try again.';
        setError(errorMessage);
      } finally {
        setLoading(false);
      }
    };
    reloadJobs();
  };

  const handleFindSimilar = async (jobId: string) => {
    setLoading(true);
    setError(null);
    setSearchSteps([
      { step: 'cv', status: 'active', message: 'Reading CV...' },
      { step: 'saved', status: 'pending', message: 'Reading latest saved jobs...' },
      { step: 'ai', status: 'pending', message: 'AI Analysis...' },
      { step: 'match', status: 'pending', message: 'Finding similar jobs...' }
    ]);
    
    try {
      // Update search steps
      setTimeout(() => {
        setSearchSteps(prev => prev.map(s => s.step === 'cv' ? { ...s, status: 'completed' as const } : s));
        setSearchSteps(prev => prev.map(s => s.step === 'saved' ? { ...s, status: 'active' as const } : s));
      }, 300);
      
      setTimeout(() => {
        setSearchSteps(prev => prev.map(s => s.step === 'saved' ? { ...s, status: 'completed' as const } : s));
        setSearchSteps(prev => prev.map(s => s.step === 'ai' ? { ...s, status: 'active' as const } : s));
      }, 600);
      
      setTimeout(() => {
        setSearchSteps(prev => prev.map(s => s.step === 'ai' ? { ...s, status: 'completed' as const } : s));
        setSearchSteps(prev => prev.map(s => s.step === 'match' ? { ...s, status: 'active' as const } : s));
      }, 900);
      
      const data = await jobsAPI.getSimilar(jobId, {
        limit: pageSize,
        hide_saved: hideSaved
      });
      
      setJobs(data.jobs || []);
      setLoadedCount(data.jobs?.length || 0);
      setTotalJobs(data.total || 0);
      setActiveSearchQuery('');
      setActiveLocationQuery('');
      setSearchQuery('');
      setLocationQuery('');
      setHasSearched(true);
      setSearchSource('similar_jobs');
      
      setSearchSteps(prev => prev.map(s => s.step === 'match' ? { ...s, status: 'completed' as const, message: `Found ${data.total || 0} similar jobs` } : s));
      
      // Load preparation statuses for jobs that are saved/applied
      loadPreparationStatuses(data.jobs || []);
    } catch (err: any) {
      console.error('Failed to find similar jobs:', err);
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to find similar jobs. Please try again.';
      setError(errorMessage);
      setSearchSteps([]);
    } finally {
      setLoading(false);
    }
  };

  // Load preparation statuses for saved/applied jobs
  const loadPreparationStatuses = async (jobsList: any[]) => {
    try {
      // Only check status for jobs that are saved/applied
      const savedJobs = jobsList.filter((job: any) => job.applied || job.application_status === 'saved' || job.application_status === 'applied' || job.application_status === 'interviewing');
      
      if (savedJobs.length === 0) return;
      
      const statusPromises = savedJobs.map(async (job: any) => {
        try {
          const status = await applicationsAPI.getPreparationStatus(job.id);
          return { jobId: job.id, status };
        } catch (err) {
          return { jobId: job.id, status: null };
        }
      });
      
      const statuses = await Promise.all(statusPromises);
      const statusMap: Record<string, any> = {};
      statuses.forEach(({ jobId, status }) => {
        if (status) {
          statusMap[jobId] = status;
        }
      });
      setPreparationStatuses(prev => ({ ...prev, ...statusMap }));
    } catch (err) {
      console.error('Failed to load preparation statuses:', err);
    }
  };

  const hasMoreJobs = loadedCount < totalJobs;

  return (
    <Layout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Browse Jobs</h1>
          <p className="text-gray-600 mt-1">Search and explore available positions</p>
        </div>

        <form onSubmit={handleSearch} className="space-y-3">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div className="md:col-span-2 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search jobs by title, company, or keywords..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div className="relative">
              <MapPin className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                placeholder="Location (e.g., New York, Remote)..."
                value={locationQuery}
                onChange={(e) => setLocationQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 items-center">
            <div className="md:col-span-2 flex items-center">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={hideSaved}
                  onChange={(e) => setHideSaved(e.target.checked)}
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700">Hide Saved Jobs</span>
              </label>
            </div>
            <div className="flex items-center justify-end gap-2">
              {(searchQuery || locationQuery || hasSearched) && (
                <button
                  type="button"
                  onClick={handleClearSearch}
                  className="flex items-center gap-2 px-4 py-2 text-sm text-gray-600 hover:text-gray-800 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
                >
                  <X className="h-4 w-4" />
                  Clear
                </button>
              )}
              <button
                type="submit"
                disabled={loading}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium shadow-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                <Search className="h-4 w-4" />
                {loading ? 'Searching...' : 'Search'}
              </button>
            </div>
          </div>
        </form>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-medium text-red-800">Error loading jobs</p>
              <p className="text-sm text-red-600 mt-1">{error}</p>
            </div>
            <button
              onClick={() => setError(null)}
              className="text-red-600 hover:text-red-800"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        )}

        {/* Search Process Steps Indicator */}
        {loading && searchSteps.length > 0 && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-3">
              <Sparkles className="h-5 w-5 text-blue-600" />
              <h3 className="text-sm font-semibold text-blue-900">Matching Process</h3>
            </div>
            <div className="space-y-2">
              {searchSteps.map((step, index) => {
                const getIcon = () => {
                  if (step.status === 'completed') {
                    return <CheckCircle2 className="h-4 w-4 text-green-600" />;
                  } else if (step.status === 'active') {
                    return <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />;
                  } else if (step.status === 'skipped') {
                    return <X className="h-4 w-4 text-gray-400" />;
                  } else {
                    return <Clock className="h-4 w-4 text-gray-400" />;
                  }
                };
                
                const getStepLabel = () => {
                  if (step.step === 'cv') return 'Reading CV';
                  if (step.step === 'saved') return 'Reading Latest Saved Jobs';
                  if (step.step === 'ai') return 'AI Analysis';
                  if (step.step === 'match') return 'Job Matching';
                  return 'Processing';
                };
                
                return (
                  <div key={index} className={`flex items-center gap-3 text-sm ${
                    step.status === 'completed' ? 'text-green-700' :
                    step.status === 'active' ? 'text-blue-700 font-medium' :
                    step.status === 'skipped' ? 'text-gray-500' :
                    'text-gray-600'
                  }`}>
                    {getIcon()}
                    <span className="flex-1">
                      <span className="font-medium">{getStepLabel()}</span>
                      {step.message && <span className="ml-2 text-gray-600">- {step.message}</span>}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}
        
        {/* Search Source Badge */}
        {!loading && searchSource && jobs.length > 0 && (
          <div className="flex items-center gap-2 text-sm">
            <span className="text-gray-600">Results from:</span>
            <span className={`px-3 py-1 rounded-full text-xs font-medium ${
              searchSource === 'cv_matches' || searchSource === 'cv_vector_search' 
                ? 'bg-green-100 text-green-800' 
                : searchSource === 'similar_to_saved'
                ? 'bg-blue-100 text-blue-800'
                : searchSource === 'vector_search' || searchSource === 'similar_jobs'
                ? 'bg-purple-100 text-purple-800'
                : 'bg-gray-100 text-gray-800'
            }`}>
              {searchSource === 'cv_matches' && '📄 CV Profile Matches'}
              {searchSource === 'cv_vector_search' && '📄 CV-Based Search'}
              {searchSource === 'similar_to_saved' && '🔖 Similar to Saved Jobs'}
              {searchSource === 'vector_search' && '🔍 Semantic Search'}
              {searchSource === 'keyword_search' && '🔎 Keyword Search'}
              {searchSource === 'similar_jobs' && '✨ Similar Jobs'}
              {searchSource === 'latest' && '📋 Latest Jobs'}
              {searchSource === 'fallback' && '📋 All Jobs'}
            </span>
          </div>
        )}

        {loading && searchSteps.length === 0 ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-2"></div>
            <div className="text-gray-500">Loading jobs...</div>
          </div>
        ) : jobs.length === 0 ? (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-12 text-center">
            <p className="text-gray-600 mb-2">
              {activeSearchQuery || activeLocationQuery 
                ? `No jobs found matching your search criteria.`
                : `No jobs found. Try adjusting your search filters.`}
            </p>
            {(activeSearchQuery || activeLocationQuery) && (
              <button
                type="button"
                onClick={handleClearSearch}
                className="text-blue-600 hover:text-blue-700 text-sm font-medium"
              >
                Clear filters and show all jobs
              </button>
            )}
          </div>
        ) : (
          <>
            <div className="grid gap-4">
              {jobs.map((job: any) => (
                <JobCard 
                  key={job.id} 
                  job={job} 
                  onApplicationUpdate={handleApplicationUpdate}
                  onFindSimilar={handleFindSimilar}
                  preparationStatus={preparationStatuses[job.id]}
                  onPrepareInterview={async (jobId: string) => {
                    try {
                      const result = await applicationsAPI.prepareInterview(jobId);
                      if (result.redirect_url) {
                        window.location.href = result.redirect_url;
                      }
                    } catch (err: any) {
                      setError(err.response?.data?.detail || 'Failed to start interview prep');
                    }
                  }}
                  onPrepareCV={async (jobId: string) => {
                    try {
                      const result = await applicationsAPI.prepareCV(jobId);
                      if (result.redirect_url) {
                        window.location.href = result.redirect_url;
                      }
                      // Reload preparation status after generating
                      const status = await applicationsAPI.getPreparationStatus(jobId);
                      setPreparationStatuses(prev => ({ ...prev, [jobId]: status }));
                    } catch (err: any) {
                      setError(err.response?.data?.detail || 'Failed to generate tailored CV');
                    }
                  }}
                  onPrepareCoverLetter={async (jobId: string) => {
                    try {
                      const result = await applicationsAPI.prepareCoverLetter(jobId);
                      if (result.redirect_url) {
                        window.location.href = result.redirect_url;
                      }
                      // Reload preparation status after generating
                      const status = await applicationsAPI.getPreparationStatus(jobId);
                      setPreparationStatuses(prev => ({ ...prev, [jobId]: status }));
                    } catch (err: any) {
                      setError(err.response?.data?.detail || 'Failed to generate cover letter');
                    }
                  }}
                />
              ))}
            </div>

            {/* Progress indicator and Load More button */}
            <div className="border-t border-gray-200 pt-6 space-y-4">
              <div className="text-sm text-gray-700 text-center">
                Showing {loadedCount} of {totalJobs} jobs
              </div>
              
              {hasMoreJobs && (
                <div className="flex justify-center">
                  <button
                    onClick={handleLoadMore}
                    disabled={loadingMore}
                    className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition font-medium"
                  >
                    {loadingMore ? (
                      <>
                        <Loader2 className="h-5 w-5 animate-spin" />
                        Loading...
                      </>
                    ) : (
                      <>
                        Load More ({totalJobs - loadedCount} remaining)
                      </>
                    )}
                  </button>
                </div>
              )}
              
              {!hasMoreJobs && totalJobs > 0 && (
                <div className="text-sm text-gray-500 text-center">
                  All jobs loaded
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </Layout>
  );
};
