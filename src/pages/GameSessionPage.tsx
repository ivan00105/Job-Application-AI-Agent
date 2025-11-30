import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { gamesAPI, Game, GameSession } from '../api/gamesClient';
import { CodingChallengePage } from './CodingChallengePage';
import { MultipleChoicePage } from './MultipleChoicePage';
import { Layout } from '../components/Layout';
import { Clock, ArrowLeft } from 'lucide-react';

export const GameSessionPage = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const [loading, setLoading] = useState(true);
  const [game, setGame] = useState<Game | null>(null);
  const [session, setSession] = useState<GameSession | null>(null);

  useEffect(() => {
    if (sessionId) {
      loadSession();
    }
  }, [sessionId]);

  const loadSession = async () => {
    if (!sessionId) return;
    
    setLoading(true);
    try {
      const { session: sessionData, game: gameData } = await gamesAPI.getSession(sessionId);
      setSession(sessionData);
      setGame(gameData);
    } catch (err) {
      console.error('Failed to load session:', err);
    } finally {
      setLoading(false);
    }
  };

  // Show loading state
  if (loading) {
    return (
      <Layout>
        <div className="max-w-4xl mx-auto">
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
            <p className="mt-4 text-gray-600">Loading challenge...</p>
          </div>
        </div>
      </Layout>
    );
  }

  // Route to specialized pages based on game type
  if (game?.game_type === 'coding') {
    return <CodingChallengePage />;
  }

  if (game?.game_type === 'multiple_choice') {
    return <MultipleChoicePage />;
  }

  // For other game types, show placeholder
  const navigate = useNavigate();
  
  return (
    <Layout>
      <div className="max-w-4xl mx-auto space-y-6">
        <button
          onClick={() => navigate('/games')}
          className="flex items-center text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Challenge Center
        </button>
        
        <div className="bg-white border rounded-xl p-8 text-center">
          <div className="mb-4">
            <Clock className="h-16 w-16 text-gray-400 mx-auto" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Challenge Session</h2>
          <p className="text-gray-600 mb-6">
            Challenge handlers for this game type ({game?.game_type || 'unknown'}) are not yet implemented. 
            Coding challenges are available now, and other types will be added soon.
          </p>
          {game && (
            <div className="text-sm text-gray-500 mb-4">
              <p>Game: {game.title}</p>
              <p>Type: {game.game_type}</p>
              <p>Session ID: {sessionId}</p>
            </div>
          )}
          <button
            onClick={() => navigate('/games')}
            className="mt-6 px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition font-medium"
          >
            Return to Challenge Center
          </button>
        </div>
      </div>
    </Layout>
  );
};

