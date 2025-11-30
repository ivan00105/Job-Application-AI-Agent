import { useState, useEffect } from 'react';
import { Layout } from '../components/Layout';
import { useNavigate } from 'react-router-dom';
import { gamesAPI, Game, GameTypeInfo, UserSessionHistoryItem, UserStatsResponse, UserGameStats, DomainStats } from '../api/gamesClient';
import { Gamepad2, Code, HelpCircle, Brain, Puzzle, Network, FileText, Filter, Search, Trophy, Star, Clock, History, Award, TrendingUp, CheckCircle, PlayCircle, XCircle, Trash2 } from 'lucide-react';

type TabType = 'browse' | 'my-challenges' | 'my-skills';

export const GameLibraryPage = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<TabType>('browse');
  
  // Browse Challenges state
  const [loading, setLoading] = useState(false);
  const [games, setGames] = useState<Game[]>([]);
  const [gameTypes, setGameTypes] = useState<GameTypeInfo[]>([]);
  const [filteredGames, setFilteredGames] = useState<Game[]>([]);
  const [selectedType, setSelectedType] = useState<string>('all');
  const [selectedDomain, setSelectedDomain] = useState<string>('all');
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  
  // My Challenges state
  const [sessionsLoading, setSessionsLoading] = useState(false);
  const [sessions, setSessions] = useState<UserSessionHistoryItem[]>([]);
  const [sessionFilterStatus, setSessionFilterStatus] = useState<string>('all');
  const [sessionFilterType, setSessionFilterType] = useState<string>('all');
  const [sessionFilterDomain, setSessionFilterDomain] = useState<string>('all');
  
  // My Skills state
  const [statsLoading, setStatsLoading] = useState(false);
  const [userStats, setUserStats] = useState<UserStatsResponse | null>(null);

  useEffect(() => {
    if (activeTab === 'browse') {
      loadData();
    } else if (activeTab === 'my-challenges') {
      if (gameTypes.length === 0) {
        // Load game types for filters
        gamesAPI.getGameTypes().then(setGameTypes).catch(console.error);
      }
      loadSessions();
    } else if (activeTab === 'my-skills') {
      loadStats();
    }
  }, [activeTab]);

  useEffect(() => {
    if (activeTab === 'browse') {
      filterGames();
    } else if (activeTab === 'my-challenges') {
      loadSessions();
    }
  }, [games, selectedType, selectedDomain, selectedDifficulty, searchQuery, sessionFilterStatus, sessionFilterType, sessionFilterDomain]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [gamesData, typesData] = await Promise.all([
        gamesAPI.getGames(),
        gamesAPI.getGameTypes(),
      ]);
      console.log('Loaded games:', gamesData.length, gamesData);
      setGames(gamesData);
      setFilteredGames(gamesData);
      setGameTypes(typesData);
    } catch (err) {
      console.error('Failed to load games:', err);
      // Show error to user
      alert('Failed to load games. Please check the console for details.');
    } finally {
      setLoading(false);
    }
  };

  const loadSessions = async () => {
    setSessionsLoading(true);
    try {
      const params: any = {};
      if (sessionFilterStatus !== 'all') params.status = sessionFilterStatus;
      if (sessionFilterType !== 'all') params.game_type = sessionFilterType;
      if (sessionFilterDomain !== 'all') params.domain = sessionFilterDomain;
      
      const sessionsData = await gamesAPI.getUserSessionsHistory(params);
      setSessions(sessionsData);
    } catch (err) {
      console.error('Failed to load sessions:', err);
    } finally {
      setSessionsLoading(false);
    }
  };

  const loadStats = async () => {
    setStatsLoading(true);
    try {
      const statsData = await gamesAPI.getUserStats();
      setUserStats(statsData);
    } catch (err) {
      console.error('Failed to load stats:', err);
    } finally {
      setStatsLoading(false);
    }
  };

  const filterGames = () => {
    let filtered = [...games];

    if (selectedType !== 'all') {
      filtered = filtered.filter(g => g.game_type === selectedType);
    }

    if (selectedDomain !== 'all') {
      filtered = filtered.filter(g => g.domain === selectedDomain || !g.domain);
    }

    if (selectedDifficulty !== 'all') {
      filtered = filtered.filter(g => g.difficulty === selectedDifficulty || !g.difficulty);
    }

    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(g => 
        g.title.toLowerCase().includes(query) ||
        g.description?.toLowerCase().includes(query) ||
        g.tags.some(tag => tag.toLowerCase().includes(query))
      );
    }

    setFilteredGames(filtered);
  };

  const [showSessionDialog, setShowSessionDialog] = useState(false);
  const [pendingGameId, setPendingGameId] = useState<string | null>(null);
  const [activeSessions, setActiveSessions] = useState<any[]>([]);

  const startGame = async (gameId: string, forceNew: boolean = false) => {
    setLoading(true);
    try {
      // Check for active sessions first (unless forcing new)
      if (!forceNew) {
        const checkResult = await gamesAPI.checkActiveSessions(gameId);
        if (checkResult.has_active_sessions && checkResult.active_sessions.length > 0) {
          setActiveSessions(checkResult.active_sessions);
          setPendingGameId(gameId);
          setShowSessionDialog(true);
          setLoading(false);
          return;
        }
      }

      // No active sessions or forcing new - start session
      const session = await gamesAPI.startSession({ game_id: gameId, force_new: forceNew });
      navigate(`/games/session/${session.id}`);
    } catch (err: any) {
      // Handle 409 conflict (active sessions exist)
      if (err.response?.status === 409) {
        const detail = err.response.data?.detail;
        if (detail?.active_sessions) {
          setActiveSessions(detail.active_sessions);
          setPendingGameId(gameId);
          setShowSessionDialog(true);
        } else {
          console.error('Failed to start game:', err);
          alert('Failed to start game session. Please try again.');
        }
      } else {
        console.error('Failed to start game:', err);
        alert('Failed to start game session. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleContinueSession = (sessionId: string) => {
    setShowSessionDialog(false);
    navigate(`/games/session/${sessionId}`);
  };

  const handleStartNew = async () => {
    if (pendingGameId) {
      setShowSessionDialog(false);
      await startGame(pendingGameId, true);
    }
  };

  const resumeSession = (sessionId: string) => {
    navigate(`/games/session/${sessionId}`);
  };

  const viewResults = (sessionId: string) => {
    navigate(`/games/results/${sessionId}`);
  };

  const deleteSession = async (sessionId: string, event?: React.MouseEvent) => {
    if (event) {
      event.stopPropagation();
    }
    
    if (!window.confirm('Are you sure you want to delete this challenge session? This action cannot be undone.')) {
      return;
    }
    
    try {
      await gamesAPI.deleteSession(sessionId);
      // Reload sessions after deletion
      loadSessions();
    } catch (err: any) {
      console.error('Failed to delete session:', err);
      alert('Failed to delete session. Please try again.');
    }
  };

  const getGameTypeIcon = (type: string) => {
    switch (type) {
      case 'coding':
        return <Code className="h-6 w-6" />;
      case 'multiple_choice':
        return <HelpCircle className="h-6 w-6" />;
      case 'personality':
        return <Brain className="h-6 w-6" />;
      case 'puzzle':
        return <Puzzle className="h-6 w-6" />;
      case 'system_design':
        return <Network className="h-6 w-6" />;
      case 'case_study':
        return <FileText className="h-6 w-6" />;
      default:
        return <Gamepad2 className="h-6 w-6" />;
    }
  };

  const getGameTypeColor = (type: string) => {
    switch (type) {
      case 'coding':
        return 'from-blue-500 to-blue-600';
      case 'multiple_choice':
        return 'from-green-500 to-green-600';
      case 'personality':
        return 'from-purple-500 to-purple-600';
      case 'puzzle':
        return 'from-orange-500 to-orange-600';
      case 'system_design':
        return 'from-indigo-500 to-indigo-600';
      case 'case_study':
        return 'from-pink-500 to-pink-600';
      default:
        return 'from-gray-500 to-gray-600';
    }
  };

  const getDifficultyColor = (difficulty?: string) => {
    switch (difficulty) {
      case 'beginner':
        return 'bg-green-100 text-green-700';
      case 'intermediate':
        return 'bg-yellow-100 text-yellow-700';
      case 'advanced':
        return 'bg-red-100 text-red-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <span className="px-2 py-1 rounded text-xs font-medium bg-green-100 text-green-700 flex items-center gap-1"><CheckCircle className="h-3 w-3" />Completed</span>;
      case 'active':
        return <span className="px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-700 flex items-center gap-1"><PlayCircle className="h-3 w-3" />In Progress</span>;
      case 'abandoned':
        return <span className="px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-700 flex items-center gap-1"><XCircle className="h-3 w-3" />Abandoned</span>;
      default:
        return <span className="px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-700">{status}</span>;
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatTime = (seconds?: number) => {
    if (!seconds) return 'N/A';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  const getSkillLevel = (avgScore: number) => {
    if (avgScore >= 90) return { level: 'Expert', color: 'text-purple-600', bgColor: 'bg-purple-100' };
    if (avgScore >= 75) return { level: 'Advanced', color: 'text-blue-600', bgColor: 'bg-blue-100' };
    if (avgScore >= 60) return { level: 'Intermediate', color: 'text-yellow-600', bgColor: 'bg-yellow-100' };
    if (avgScore >= 40) return { level: 'Beginner', color: 'text-green-600', bgColor: 'bg-green-100' };
    return { level: 'Novice', color: 'text-gray-600', bgColor: 'bg-gray-100' };
  };

  return (
    <Layout>
      <div className="space-y-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <Gamepad2 className="h-8 w-8 text-purple-600" />
            Challenge Center
          </h1>
          <p className="text-gray-600 mt-2">
            Prove your skills through interactive challenges and assessments
          </p>
        </div>

        {/* Tabs */}
        <div className="bg-white border rounded-xl overflow-hidden">
          <div className="flex border-b">
            <button
              onClick={() => setActiveTab('browse')}
              className={`flex-1 px-6 py-4 text-center font-medium transition ${
                activeTab === 'browse'
                  ? 'bg-purple-50 text-purple-600 border-b-2 border-purple-600'
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              <div className="flex items-center justify-center gap-2">
                <Gamepad2 className="h-5 w-5" />
                Browse Challenges
              </div>
            </button>
            <button
              onClick={() => setActiveTab('my-challenges')}
              className={`flex-1 px-6 py-4 text-center font-medium transition ${
                activeTab === 'my-challenges'
                  ? 'bg-purple-50 text-purple-600 border-b-2 border-purple-600'
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              <div className="flex items-center justify-center gap-2">
                <History className="h-5 w-5" />
                My Challenges
              </div>
            </button>
            <button
              onClick={() => setActiveTab('my-skills')}
              className={`flex-1 px-6 py-4 text-center font-medium transition ${
                activeTab === 'my-skills'
                  ? 'bg-purple-50 text-purple-600 border-b-2 border-purple-600'
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              <div className="flex items-center justify-center gap-2">
                <TrendingUp className="h-5 w-5" />
                My Skills
              </div>
            </button>
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {/* Browse Challenges Tab */}
            {activeTab === 'browse' && (
              <>
                {/* Filters */}
                <div className="mb-6">
                  <div className="flex items-center gap-4 mb-4">
                    <Filter className="h-5 w-5 text-gray-600" />
                    <h2 className="text-lg font-semibold text-gray-900">Filters</h2>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Search</label>
                      <div className="relative">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                        <input
                          type="text"
                          placeholder="Search challenges..."
                          value={searchQuery}
                          onChange={(e) => setSearchQuery(e.target.value)}
                          className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                        />
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Challenge Type</label>
                      <select
                        value={selectedType}
                        onChange={(e) => setSelectedType(e.target.value)}
                        className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      >
                        <option value="all">All Types</option>
                        {gameTypes.map(type => (
                          <option key={type.type_code} value={type.type_code}>
                            {type.name}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Domain</label>
                      <select
                        value={selectedDomain}
                        onChange={(e) => setSelectedDomain(e.target.value)}
                        className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      >
                        <option value="all">All Domains</option>
                        <option value="IT">IT</option>
                        <option value="Finance">Finance</option>
                        <option value="General">General</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Difficulty</label>
                      <select
                        value={selectedDifficulty}
                        onChange={(e) => setSelectedDifficulty(e.target.value)}
                        className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      >
                        <option value="all">All Levels</option>
                        <option value="beginner">Beginner</option>
                        <option value="intermediate">Intermediate</option>
                        <option value="advanced">Advanced</option>
                      </select>
                    </div>
                  </div>
                </div>

                {/* Games Grid */}
                {loading && games.length === 0 ? (
                  <div className="text-center py-12">
                    <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
                    <p className="mt-4 text-gray-600">Loading games...</p>
                  </div>
                ) : filteredGames.length === 0 ? (
                  <div className="bg-white border rounded-xl p-12 text-center">
                    <Gamepad2 className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">No challenges found</h3>
                    <p className="text-gray-600">
                      {games.length === 0 
                        ? "Challenges will appear here once they're added to the library."
                        : "Try adjusting your filters to see more challenges."}
                    </p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {filteredGames.map((game) => (
                      <div
                        key={game.id}
                        className="bg-white border rounded-xl p-6 hover:shadow-lg transition-all cursor-pointer group"
                        onClick={() => startGame(game.id)}
                      >
                        <div className={`bg-gradient-to-br ${getGameTypeColor(game.game_type)} text-white p-4 rounded-lg mb-4 inline-flex`}>
                          {getGameTypeIcon(game.game_type)}
                        </div>
                        
                        <h3 className="text-xl font-bold text-gray-900 mb-2 group-hover:text-purple-600 transition">
                          {game.title}
                        </h3>
                        
                        <p className="text-gray-600 text-sm mb-4 line-clamp-2">
                          {game.description || 'Test your skills with this challenge'}
                        </p>

                        <div className="flex flex-wrap gap-2 mb-4">
                          {game.difficulty && (
                            <span className={`px-2 py-1 rounded text-xs font-medium ${getDifficultyColor(game.difficulty)}`}>
                              {game.difficulty}
                            </span>
                          )}
                          {game.domain && (
                            <span className="px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-700">
                              {game.domain}
                            </span>
                          )}
                          {game.time_limit_minutes && (
                            <span className="px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-700 flex items-center gap-1">
                              <Clock className="h-3 w-3" />
                              {game.time_limit_minutes}m
                            </span>
                          )}
                        </div>

                        <div className="flex items-center justify-between pt-4 border-t">
                          <div className="flex items-center gap-2 text-sm text-gray-600">
                            <Trophy className="h-4 w-4" />
                            <span>{game.points} points</span>
                          </div>
                          <button
                            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition font-medium text-sm"
                            onClick={(e) => {
                              e.stopPropagation();
                              startGame(game.id);
                            }}
                          >
                            Start
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}

            {/* My Challenges Tab */}
            {activeTab === 'my-challenges' && (
              <>
                {/* Filters */}
                <div className="mb-6">
                  <div className="flex items-center gap-4 mb-4">
                    <Filter className="h-5 w-5 text-gray-600" />
                    <h2 className="text-lg font-semibold text-gray-900">Filters</h2>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
                      <select
                        value={sessionFilterStatus}
                        onChange={(e) => setSessionFilterStatus(e.target.value)}
                        className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      >
                        <option value="all">All Status</option>
                        <option value="completed">Completed</option>
                        <option value="active">In Progress</option>
                        <option value="abandoned">Abandoned</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Challenge Type</label>
                      <select
                        value={sessionFilterType}
                        onChange={(e) => setSessionFilterType(e.target.value)}
                        className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      >
                        <option value="all">All Types</option>
                        {gameTypes.map(type => (
                          <option key={type.type_code} value={type.type_code}>
                            {type.name}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Domain</label>
                      <select
                        value={sessionFilterDomain}
                        onChange={(e) => setSessionFilterDomain(e.target.value)}
                        className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      >
                        <option value="all">All Domains</option>
                        <option value="IT">IT</option>
                        <option value="Finance">Finance</option>
                        <option value="General">General</option>
                      </select>
                    </div>
                  </div>
                </div>

                {/* Sessions List */}
                {sessionsLoading ? (
                  <div className="text-center py-12">
                    <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
                    <p className="mt-4 text-gray-600">Loading your challenges...</p>
                  </div>
                ) : sessions.length === 0 ? (
                  <div className="bg-white border rounded-xl p-12 text-center">
                    <History className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">No challenges yet</h3>
                    <p className="text-gray-600 mb-4">
                      Start a challenge from the Browse Challenges tab to see your history here.
                    </p>
                    <button
                      onClick={() => setActiveTab('browse')}
                      className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition"
                    >
                      Browse Challenges
                    </button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {sessions.map((session) => (
                      <div
                        key={session.id}
                        className="bg-white border rounded-xl p-6 hover:shadow-md transition"
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                              <div className={`bg-gradient-to-br ${getGameTypeColor(session.game_type)} text-white p-2 rounded-lg`}>
                                {getGameTypeIcon(session.game_type)}
                              </div>
                              <h3 className="text-xl font-bold text-gray-900">{session.title}</h3>
                            </div>
                            
                            <div className="flex flex-wrap items-center gap-3 mb-4">
                              {getStatusBadge(session.status)}
                              {session.domain && (
                                <span className="px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-700">
                                  {session.domain}
                                </span>
                              )}
                              {session.difficulty && (
                                <span className={`px-2 py-1 rounded text-xs font-medium ${getDifficultyColor(session.difficulty)}`}>
                                  {session.difficulty}
                                </span>
                              )}
                            </div>

                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-gray-600">
                              <div>
                                <span className="font-medium">Started:</span> {formatDate(session.started_at)}
                              </div>
                              {session.completed_at && (
                                <div>
                                  <span className="font-medium">Completed:</span> {formatDate(session.completed_at)}
                                </div>
                              )}
                              {session.time_taken_seconds && (
                                <div>
                                  <span className="font-medium">Time:</span> {formatTime(session.time_taken_seconds)}
                                </div>
                              )}
                              {session.score !== undefined && (
                                <div>
                                  <span className="font-medium">Score:</span> <span className="font-bold text-purple-600">{session.score}</span> / {session.points}
                                </div>
                              )}
                            </div>
                          </div>

                          <div className="flex flex-col gap-2 ml-4">
                            <div className="flex gap-2">
                              {session.status === 'active' && (
                                <button
                                  onClick={() => resumeSession(session.id)}
                                  className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition font-medium text-sm whitespace-nowrap"
                                >
                                  Resume
                                </button>
                              )}
                              {session.status === 'completed' && (
                                <button
                                  onClick={() => viewResults(session.id)}
                                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition font-medium text-sm whitespace-nowrap"
                                >
                                  View Results
                                </button>
                              )}
                              <button
                                onClick={(e) => deleteSession(session.id, e)}
                                className="px-3 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition font-medium text-sm whitespace-nowrap flex items-center gap-1"
                                title="Delete session"
                              >
                                <Trash2 className="h-4 w-4" />
                              </button>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}

            {/* My Skills Tab */}
            {activeTab === 'my-skills' && (
              <>
                {statsLoading ? (
                  <div className="text-center py-12">
                    <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
                    <p className="mt-4 text-gray-600">Loading your skills...</p>
                  </div>
                ) : !userStats ? (
                  <div className="bg-white border rounded-xl p-12 text-center">
                    <TrendingUp className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">No skills data yet</h3>
                    <p className="text-gray-600">
                      Complete some challenges to see your skills breakdown here.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-8">
                    {/* Overall Stats */}
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                      <div className="bg-gradient-to-br from-purple-500 to-purple-600 text-white rounded-xl p-6">
                        <div className="text-3xl font-bold">{userStats.total_games_played}</div>
                        <div className="text-purple-100 mt-1">Challenges Played</div>
                      </div>
                      <div className="bg-gradient-to-br from-blue-500 to-blue-600 text-white rounded-xl p-6">
                        <div className="text-3xl font-bold">{userStats.total_score}</div>
                        <div className="text-blue-100 mt-1">Total Score</div>
                      </div>
                      <div className="bg-gradient-to-br from-yellow-500 to-yellow-600 text-white rounded-xl p-6">
                        <div className="text-3xl font-bold">{userStats.total_badges}</div>
                        <div className="text-yellow-100 mt-1">Badges Earned</div>
                      </div>
                      <div className="bg-gradient-to-br from-green-500 to-green-600 text-white rounded-xl p-6">
                        <div className="text-3xl font-bold">
                          {userStats.total_games_played > 0 
                            ? Math.round(userStats.total_score / userStats.total_games_played)
                            : 0}
                        </div>
                        <div className="text-green-100 mt-1">Avg Score</div>
                      </div>
                    </div>

                    {/* Skills by Game Type */}
                    {Object.keys(userStats.stats_by_type).length > 0 && (
                      <div>
                        <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                          <Code className="h-6 w-6 text-purple-600" />
                          Skills by Challenge Type
                        </h2>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                          {Object.entries(userStats.stats_by_type).map(([gameType, stats]: [string, UserGameStats]) => {
                            const skillLevel = getSkillLevel(stats.avg_score || 0);
                            return (
                              <div key={gameType} className="bg-white border rounded-xl p-6">
                                <div className="flex items-center gap-3 mb-4">
                                  <div className={`bg-gradient-to-br ${getGameTypeColor(gameType)} text-white p-3 rounded-lg`}>
                                    {getGameTypeIcon(gameType)}
                                  </div>
                                  <div>
                                    <h3 className="font-bold text-gray-900 capitalize">{gameType.replace('_', ' ')}</h3>
                                    <span className={`px-2 py-1 rounded text-xs font-medium ${skillLevel.bgColor} ${skillLevel.color}`}>
                                      {skillLevel.level}
                                    </span>
                                  </div>
                                </div>
                                
                                <div className="space-y-3">
                                  <div>
                                    <div className="flex justify-between text-sm mb-1">
                                      <span className="text-gray-600">Challenges Completed</span>
                                      <span className="font-medium">{stats.games_completed}</span>
                                    </div>
                                    <div className="w-full bg-gray-200 rounded-full h-2">
                                      <div 
                                        className="bg-purple-600 h-2 rounded-full transition-all"
                                        style={{ width: `${Math.min((stats.games_completed / Math.max(stats.total_games_played, 1)) * 100, 100)}%` }}
                                      ></div>
                                    </div>
                                  </div>
                                  
                                  <div className="grid grid-cols-2 gap-2 text-sm">
                                    <div>
                                      <div className="text-gray-600">Avg Score</div>
                                      <div className="font-bold text-lg">{Math.round(stats.avg_score || 0)}</div>
                                    </div>
                                    <div>
                                      <div className="text-gray-600">Best Score</div>
                                      <div className="font-bold text-lg text-purple-600">{stats.best_score || 0}</div>
                                    </div>
                                  </div>
                                  
                                  {stats.badges_earned > 0 && (
                                    <div className="flex items-center gap-2 text-sm">
                                      <Award className="h-4 w-4 text-yellow-500" />
                                      <span>{stats.badges_earned} badge{stats.badges_earned !== 1 ? 's' : ''} earned</span>
                                    </div>
                                  )}
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    {/* Skills by Domain */}
                    {userStats.stats_by_domain && Object.keys(userStats.stats_by_domain).length > 0 && (
                      <div>
                        <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                          <Network className="h-6 w-6 text-purple-600" />
                          Skills by Domain
                        </h2>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                          {Object.entries(userStats.stats_by_domain).map(([domain, stats]: [string, DomainStats]) => {
                            const skillLevel = getSkillLevel(stats.avg_score);
                            return (
                              <div key={domain} className="bg-white border rounded-xl p-6">
                                <div className="mb-4">
                                  <h3 className="font-bold text-gray-900 text-lg">{domain}</h3>
                                  <span className={`px-2 py-1 rounded text-xs font-medium ${skillLevel.bgColor} ${skillLevel.color}`}>
                                    {skillLevel.level}
                                  </span>
                                </div>
                                
                                <div className="space-y-3">
                                  <div>
                                    <div className="flex justify-between text-sm mb-1">
                                      <span className="text-gray-600">Challenges Completed</span>
                                      <span className="font-medium">{stats.completed_challenges} / {stats.total_challenges}</span>
                                    </div>
                                    <div className="w-full bg-gray-200 rounded-full h-2">
                                      <div 
                                        className="bg-blue-600 h-2 rounded-full transition-all"
                                        style={{ width: `${Math.min((stats.completed_challenges / Math.max(stats.total_challenges, 1)) * 100, 100)}%` }}
                                      ></div>
                                    </div>
                                  </div>
                                  
                                  <div className="grid grid-cols-2 gap-2 text-sm">
                                    <div>
                                      <div className="text-gray-600">Avg Score</div>
                                      <div className="font-bold text-lg">{Math.round(stats.avg_score)}</div>
                                    </div>
                                    <div>
                                      <div className="text-gray-600">Best Score</div>
                                      <div className="font-bold text-lg text-blue-600">{stats.best_score}</div>
                                    </div>
                                  </div>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    {/* Badges Section */}
                    {userStats.badges && userStats.badges.length > 0 && (
                      <div>
                        <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                          <Award className="h-6 w-6 text-yellow-500" />
                          Earned Badges
                        </h2>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                          {userStats.badges.map((badge) => (
                            <div key={badge.id} className="bg-white border rounded-xl p-4 flex items-center gap-3">
                              <div className="p-2 bg-yellow-100 rounded-full">
                                <Award className="h-6 w-6 text-yellow-600" />
                              </div>
                              <div className="flex-1">
                                <div className="font-medium text-gray-900">{badge.badge_type}</div>
                                {badge.game_type && (
                                  <div className="text-sm text-gray-600 capitalize">{badge.game_type.replace('_', ' ')}</div>
                                )}
                                {badge.earned_at && (
                                  <div className="text-xs text-gray-500">{formatDate(badge.earned_at)}</div>
                                )}
                              </div>
                              {badge.verified && (
                                <CheckCircle className="h-5 w-5 text-green-500" />
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </>
            )}
          </div>
        </div>

        {/* Info Section - Only show on Browse tab */}
        {activeTab === 'browse' && (
          <div className="bg-purple-50 border border-purple-200 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <Star className="h-5 w-5 text-purple-600" />
              About Challenge Center
            </h3>
            <p className="text-gray-700 mb-4">
              The Challenge Center is your place to demonstrate your skills beyond your CV. 
              Complete challenges, earn badges, and climb leaderboards to prove your abilities to employers.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
              <div className="bg-white rounded-lg p-4">
                <Trophy className="h-6 w-6 text-yellow-500 mb-2" />
                <h4 className="font-semibold text-gray-900 mb-1">Earn Badges</h4>
                <p className="text-sm text-gray-600">Complete challenges to earn verified skill badges</p>
              </div>
              <div className="bg-white rounded-lg p-4">
                <Gamepad2 className="h-6 w-6 text-purple-500 mb-2" />
                <h4 className="font-semibold text-gray-900 mb-1">Multiple Challenge Types</h4>
                <p className="text-sm text-gray-600">Coding, quizzes, puzzles, and more coming soon</p>
              </div>
              <div className="bg-white rounded-lg p-4">
                <Brain className="h-6 w-6 text-blue-500 mb-2" />
                <h4 className="font-semibold text-gray-900 mb-1">Prove Your Skills</h4>
                <p className="text-sm text-gray-600">Show employers your real abilities, not just AI-polished CVs</p>
              </div>
            </div>
          </div>
        )}
      </div>
      {/* Active Sessions Dialog */}
      {showSessionDialog && activeSessions.length > 0 && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full mx-4 p-6">
            <h3 className="text-xl font-bold text-gray-900 mb-4">
              Unfinished Session Found
            </h3>
            <p className="text-gray-600 mb-4">
              You have {activeSessions.length} unfinished session{activeSessions.length > 1 ? 's' : ''} for this challenge. 
              Would you like to continue or start a new one?
            </p>
            
            <div className="space-y-3 mb-6">
              {activeSessions.map((session) => (
                <div key={session.id} className="border rounded-lg p-3 bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium text-gray-900">
                        Started {session.started_at ? new Date(session.started_at).toLocaleString() : 'Unknown'}
                      </div>
                      {session.score !== null && (
                        <div className="text-sm text-gray-600">
                          Current Score: {session.score}
                        </div>
                      )}
                    </div>
                    <button
                      onClick={() => handleContinueSession(session.id)}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                    >
                      Continue
                    </button>
                  </div>
                </div>
              ))}
            </div>

            <div className="flex gap-3">
              <button
                onClick={handleStartNew}
                className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors"
              >
                Start New Session
              </button>
              <button
                onClick={() => {
                  setShowSessionDialog(false);
                  setPendingGameId(null);
                  setActiveSessions([]);
                }}
                className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </Layout>
  );
};
