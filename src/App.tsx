import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { JobsPage } from './pages/JobsPage';
import { ApplicationsPage } from './pages/ApplicationsPage';
import { ProfilePage } from './pages/ProfilePage';
import { InterviewSessionPage } from './pages/InterviewSessionPage';
import { InterviewResultsPage } from './pages/InterviewResultsPage';
import { InterviewAnalyticsPage } from './pages/InterviewAnalyticsPage';
import { InterviewManagementPage } from './pages/InterviewManagementPage';
import { TailoredCVPage } from './pages/TailoredCVPage';
import { CoverLetterPage } from './pages/CoverLetterPage';
import { MemoryManagementPage } from './pages/MemoryManagementPage';
import './index.css';

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/jobs"
            element={
              <ProtectedRoute>
                <JobsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/applications"
            element={
              <ProtectedRoute>
                <ApplicationsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <ProfilePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/interview"
            element={
              <ProtectedRoute>
                <Navigate to="/interviews" replace />
              </ProtectedRoute>
            }
          />
          <Route
            path="/interview/session/:sessionId"
            element={
              <ProtectedRoute>
                <InterviewSessionPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/interview/session/:sessionId/results"
            element={
              <ProtectedRoute>
                <InterviewResultsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/interview/analytics"
            element={
              <ProtectedRoute>
                <InterviewAnalyticsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/interviews"
            element={
              <ProtectedRoute>
                <InterviewManagementPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/applications/prepare/cv/:id"
            element={
              <ProtectedRoute>
                <TailoredCVPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/applications/prepare/cover-letter/:id"
            element={
              <ProtectedRoute>
                <CoverLetterPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/memory"
            element={
              <ProtectedRoute>
                <MemoryManagementPage />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
