import { FaRobot, FaLock, FaEnvelope } from "react-icons/fa";

export default function Login() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-slate-900 to-purple-950 flex items-center justify-center px-6">

      <div className="w-full max-w-6xl grid md:grid-cols-2 overflow-hidden rounded-3xl shadow-2xl border border-purple-500/20">

        {/* Left Side */}
        <div className="hidden md:flex flex-col justify-center p-12 text-white bg-black/20 backdrop-blur-lg">

          <div className="flex items-center gap-3 mb-6">
            <FaRobot className="text-5xl text-purple-400" />
            <h1 className="text-5xl font-bold">
              RAG <span className="text-purple-400">Chatbot</span>
            </h1>
          </div>

          <p className="text-gray-300 text-lg mb-10">
            Ask Anything. Get Intelligent Answers.
          </p>

          <div className="space-y-6">

            <div>
              <h3 className="font-semibold text-xl">
                📄 Upload Documents
              </h3>
              <p className="text-gray-400">
                Upload PDFs and knowledge files.
              </p>
            </div>

            <div>
              <h3 className="font-semibold text-xl">
                🔍 Semantic Search
              </h3>
              <p className="text-gray-400">
                Find relevant information instantly.
              </p>
            </div>

            <div>
              <h3 className="font-semibold text-xl">
                🤖 AI Powered Answers
              </h3>
              <p className="text-gray-400">
                Get contextual responses from your data.
              </p>
            </div>

            <div>
              <h3 className="font-semibold text-xl">
                💬 Session Management
              </h3>
              <p className="text-gray-400">
                Save and continue conversations.
              </p>
            </div>

          </div>
        </div>

        {/* Right Side */}
        <div className="bg-white/5 backdrop-blur-xl p-10">

          <div className="max-w-md mx-auto">

            <h2 className="text-4xl font-bold text-white text-center">
              Welcome Back 👋
            </h2>

            <p className="text-gray-400 text-center mt-2">
              Login to continue
            </p>

            <form className="mt-10 space-y-5">

              <div>
                <label className="text-gray-300 text-sm">
                  Email
                </label>

                <div className="mt-2 flex items-center bg-white/10 rounded-xl px-4">
                  <FaEnvelope className="text-purple-400" />
                  <input
                    type="email"
                    placeholder="Enter your email"
                    className="w-full bg-transparent p-4 outline-none text-white"
                  />
                </div>
              </div>

              <div>
                <label className="text-gray-300 text-sm">
                  Password
                </label>

                <div className="mt-2 flex items-center bg-white/10 rounded-xl px-4">
                  <FaLock className="text-purple-400" />
                  <input
                    type="password"
                    placeholder="Enter password"
                    className="w-full bg-transparent p-4 outline-none text-white"
                  />
                </div>
              </div>

              <button
                className="w-full py-4 rounded-xl bg-gradient-to-r from-violet-600 to-purple-500 text-white font-semibold hover:scale-105 transition"
              >
                Login
              </button>

            </form>

            <p className="text-center text-gray-400 mt-6">
              Don't have an account?
              <span className="text-purple-400 cursor-pointer ml-2">
                Sign Up
              </span>
            </p>

          </div>
        </div>

      </div>
    </div>
  );
}