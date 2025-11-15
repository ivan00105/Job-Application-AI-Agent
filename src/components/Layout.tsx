/**
 * Layout Component
 * Main layout with navigation
 */
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { LogOut, FileText, Briefcase, Target, User, Bookmark, MessageSquare } from 'lucide-react';

export const Layout = ({ children }: { children: React.ReactNode }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex">
              <Link to="/" className="flex items-center">
                <Briefcase className="h-8 w-8 text-blue-600" />
                <span className="ml-2 text-xl font-bold text-gray-900">
                  Job Agent
                </span>
              </Link>

              <div className="ml-10 flex items-center space-x-4">
                <Link
                  to="/"
                  className="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium flex items-center"
                >
                  <Target className="h-4 w-4 mr-1" />
                  Matches
                </Link>
                <Link
                  to="/jobs"
                  className="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium flex items-center"
                >
                  <Briefcase className="h-4 w-4 mr-1" />
                  Jobs
                </Link>
                <Link
                  to="/applications"
                  className="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium flex items-center"
                >
                  <Bookmark className="h-4 w-4 mr-1" />
                  Saved Jobs
                </Link>
                <Link
                  to="/interviews"
                  className="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium flex items-center"
                >
                  <MessageSquare className="h-4 w-4 mr-1" />
                  Interviews
                </Link>
                <Link
                  to="/profile"
                  className="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium flex items-center"
                >
                  <FileText className="h-4 w-4 mr-1" />
                  Profile
                </Link>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-700 flex items-center">
                <User className="h-4 w-4 mr-1" />
                {user?.username}
              </span>
              <button
                onClick={handleLogout}
                className="flex items-center text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
              >
                <LogOut className="h-4 w-4 mr-1" />
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
    </div>
  );
};
