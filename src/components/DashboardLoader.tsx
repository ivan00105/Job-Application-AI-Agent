/**
 * Dashboard Loader Component
 * A stunning loading page for the dashboard with smooth animations
 */
import { 
  Briefcase, 
  TrendingUp, 
  Target, 
  Sparkles, 
  BarChart3,
  Zap,
  CheckCircle2
} from 'lucide-react';

export const DashboardLoader = () => {
  return (
    <div className="fixed inset-0 z-50 bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 overflow-hidden">
      {/* Animated background blobs */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-0 left-0 w-96 h-96 bg-blue-300 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob"></div>
        <div className="absolute top-0 right-0 w-96 h-96 bg-purple-300 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-2000"></div>
        <div className="absolute bottom-0 left-1/2 w-96 h-96 bg-indigo-300 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-4000"></div>
      </div>

      {/* Grid pattern overlay */}
      <div className="absolute inset-0 bg-grid-pattern opacity-5"></div>

      {/* Main content */}
      <div className="relative z-10 flex items-center justify-center min-h-screen px-4">
        <div className="text-center max-w-2xl w-full">
          {/* Logo/Icon section */}
          <div className="mb-8 flex justify-center">
            <div className="relative">
              {/* Outer pulsing ring */}
              <div className="absolute inset-0 border-4 border-blue-200 rounded-full animate-ping opacity-75"></div>
              
              {/* Main icon container */}
              <div className="relative w-32 h-32 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-2xl transform hover:scale-105 transition-transform duration-300">
                <Briefcase className="w-16 h-16 text-white" />
                
                {/* Sparkles around icon */}
                <div className="absolute -top-2 -right-2">
                  <Sparkles className="w-6 h-6 text-yellow-400 animate-pulse" />
                </div>
                <div className="absolute -bottom-2 -left-2">
                  <Zap className="w-5 h-5 text-blue-300 animate-pulse animation-delay-1000" />
                </div>
                <div className="absolute top-0 -left-4">
                  <Target className="w-4 h-4 text-purple-300 animate-pulse animation-delay-2000" />
                </div>
              </div>

              {/* Rotating ring */}
              <div className="absolute inset-0 border-4 border-transparent border-t-blue-600 rounded-full animate-spin-slow"></div>
            </div>
          </div>

          {/* Title */}
          <h1 className="text-5xl font-bold text-gray-900 mb-4 animate-fade-in">
            <span className="bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-600 bg-clip-text text-transparent">
              Loading Your Dashboard
            </span>
          </h1>

          {/* Subtitle */}
          <p className="text-xl text-gray-600 mb-12 animate-fade-in animation-delay-300">
            Preparing your personalized job search hub...
          </p>

          {/* Loading steps */}
          <div className="space-y-4 mb-12">
            {[
              { icon: Briefcase, text: 'Fetching job recommendations', delay: '0s', completed: false },
              { icon: BarChart3, text: 'Analyzing your profile', delay: '0.2s', completed: false },
              { icon: TrendingUp, text: 'Calculating match scores', delay: '0.4s', completed: false },
              { icon: Target, text: 'Preparing insights', delay: '0.6s', completed: false },
            ].map((step, index) => (
              <div
                key={index}
                className="flex items-center justify-center gap-4 p-4 bg-white/70 backdrop-blur-md rounded-xl shadow-xl border border-white/30 animate-slide-in hover:bg-white/80 transition-all duration-300"
                style={{ animationDelay: step.delay }}
              >
                <div className="relative flex-shrink-0">
                  <step.icon className="w-6 h-6 text-blue-600 relative z-10" />
                  {!step.completed && (
                    <div className="absolute inset-0 bg-blue-200 rounded-full animate-ping opacity-50"></div>
                  )}
                </div>
                <span className="text-gray-800 font-medium flex-1 text-left">{step.text}</span>
                <div className="ml-auto flex-shrink-0">
                  {step.completed ? (
                    <CheckCircle2 className="w-5 h-5 text-green-600" />
                  ) : (
                    <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse"></div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Progress bar */}
          <div className="mb-8">
            <div className="h-2.5 bg-white/40 rounded-full overflow-hidden shadow-inner backdrop-blur-sm">
              <div className="h-full bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-600 rounded-full animate-progress shadow-lg"></div>
            </div>
            <p className="text-sm text-gray-600 mt-3 font-medium">This will only take a moment...</p>
          </div>

          {/* Animated dots */}
          <div className="flex justify-center gap-2">
            {[0, 1, 2].map((i) => (
              <div
                key={i}
                className="w-3 h-3 bg-blue-600 rounded-full animate-bounce"
                style={{ animationDelay: `${i * 0.2}s` }}
              ></div>
            ))}
          </div>
        </div>
      </div>

      {/* Floating particles */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {[...Array(20)].map((_, i) => (
          <div
            key={i}
            className="absolute w-2 h-2 bg-blue-400 rounded-full opacity-20 animate-float"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 5}s`,
              animationDuration: `${3 + Math.random() * 4}s`,
            }}
          ></div>
        ))}
      </div>

      {/* Custom animations */}
      <style>{`
        @keyframes blob {
          0%, 100% {
            transform: translate(0, 0) scale(1);
          }
          33% {
            transform: translate(30px, -50px) scale(1.1);
          }
          66% {
            transform: translate(-20px, 20px) scale(0.9);
          }
        }
        
        @keyframes fade-in {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        @keyframes slide-in {
          from {
            opacity: 0;
            transform: translateX(-20px);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }
        
        @keyframes progress {
          0% {
            width: 0%;
          }
          50% {
            width: 70%;
          }
          100% {
            width: 100%;
          }
        }
        
        @keyframes float {
          0%, 100% {
            transform: translateY(0) rotate(0deg);
            opacity: 0.2;
          }
          50% {
            transform: translateY(-20px) rotate(180deg);
            opacity: 0.4;
          }
        }
        
        .animate-blob {
          animation: blob 7s infinite;
        }
        
        .animation-delay-2000 {
          animation-delay: 2s;
        }
        
        .animation-delay-4000 {
          animation-delay: 4s;
        }
        
        .animation-delay-1000 {
          animation-delay: 1s;
        }
        
        .animation-delay-300 {
          animation-delay: 0.3s;
        }
        
        .animate-fade-in {
          animation: fade-in 0.8s ease-out;
        }
        
        .animate-slide-in {
          animation: slide-in 0.6s ease-out forwards;
          opacity: 0;
        }
        
        .animate-progress {
          animation: progress 2s ease-in-out infinite;
          box-shadow: 0 0 10px rgba(59, 130, 246, 0.5);
        }
        
        .animate-float {
          animation: float 3s ease-in-out infinite;
        }
        
        .animate-spin-slow {
          animation: spin 3s linear infinite;
        }
        
        .bg-grid-pattern {
          background-image: 
            linear-gradient(to right, rgba(0, 0, 0, 0.1) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(0, 0, 0, 0.1) 1px, transparent 1px);
          background-size: 50px 50px;
        }
      `}</style>
    </div>
  );
};

