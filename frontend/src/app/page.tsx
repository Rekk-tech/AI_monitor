import Link from 'next/link';

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 flex items-center justify-center">
      <div className="text-center max-w-2xl mx-auto px-6">
        {/* Logo */}
        <div className="mb-8">
          <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg shadow-blue-500/20">
            <span className="text-white font-bold text-3xl">AI</span>
          </div>
          <h1 className="text-4xl font-bold text-white mb-2">AI Monitor</h1>
          <p className="text-gray-400 text-lg">
            Real-time Customer Satisfaction Analysis
          </p>
        </div>

        {/* Description */}
        <p className="text-gray-300 mb-8 leading-relaxed">
          Monitor customer calls in real-time with AI-powered video and audio emotion analysis.
          Get instant satisfaction scores and actionable insights.
        </p>

        {/* Features */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
          <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
            <div className="text-2xl mb-2">🎥</div>
            <h3 className="text-white font-semibold">Video Analysis</h3>
            <p className="text-sm text-gray-400">Face emotion detection</p>
          </div>
          <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
            <div className="text-2xl mb-2">🎤</div>
            <h3 className="text-white font-semibold">Audio Analysis</h3>
            <p className="text-sm text-gray-400">Speech emotion recognition</p>
          </div>
          <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
            <div className="text-2xl mb-2">📊</div>
            <h3 className="text-white font-semibold">AI Agent</h3>
            <p className="text-sm text-gray-400">Combined satisfaction score</p>
          </div>
        </div>

        {/* CTA */}
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-semibold py-3 px-8 rounded-lg transition-all shadow-lg shadow-blue-500/25"
        >
          Open Dashboard
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
          </svg>
        </Link>

        {/* Footer */}
        <p className="text-gray-500 text-sm mt-8">
          Backend running on <code className="text-gray-400">http://localhost:8000</code>
        </p>
      </div>
    </div>
  );
}
