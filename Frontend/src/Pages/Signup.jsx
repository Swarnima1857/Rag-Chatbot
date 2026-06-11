import { FaRobot, FaLock, FaEnvelope, FaUser } from "react-icons/fa";

export default function Signup() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-slate-900 to-purple-950 flex items-center justify-center px-6">

      <div className="w-full max-w-6xl grid md:grid-cols-2 overflow-hidden rounded-3xl shadow-2xl border border-purple-500/20">

        {/* Left Side Same */}

        <div className="hidden md:flex flex-col justify-center p-12 text-white">
          <FaRobot className="text-7xl text-purple-400 mb-5" />

          <h1 className="text-5xl font-bold">
            RAG <span className="text-purple-400">Chatbot</span>
          </h1>

          <p className="mt-4 text-gray-300">
            Upload PDFs. Search Semantically. Chat with AI.
          </p>
        </div>

        {/* Right Side */}

        <div className="bg-white/5 backdrop-blur-xl p-10">

          <div className="max-w-md mx-auto">

            <h2 className="text-4xl text-center text-white font-bold">
              Create Account ✨
            </h2>

            <form className="space-y-5 mt-10">

              <div className="flex items-center bg-white/10 rounded-xl px-4">
                <FaUser className="text-purple-400" />
                <input
                  type="text"
                  placeholder="Full Name"
                  className="w-full bg-transparent p-4 outline-none text-white"
                />
              </div>

              <div className="flex items-center bg-white/10 rounded-xl px-4">
                <FaEnvelope className="text-purple-400" />
                <input
                  type="email"
                  placeholder="Email"
                  className="w-full bg-transparent p-4 outline-none text-white"
                />
              </div>

              <div className="flex items-center bg-white/10 rounded-xl px-4">
                <FaLock className="text-purple-400" />
                <input
                  type="password"
                  placeholder="Password"
                  className="w-full bg-transparent p-4 outline-none text-white"
                />
              </div>

              <div className="flex items-center bg-white/10 rounded-xl px-4">
                <FaLock className="text-purple-400" />
                <input
                  type="password"
                  placeholder="Confirm Password"
                  className="w-full bg-transparent p-4 outline-none text-white"
                />
              </div>

              <button
                className="w-full py-4 rounded-xl bg-gradient-to-r from-violet-600 to-purple-500 text-white font-semibold hover:scale-105 transition"
              >
                Create Account
              </button>

            </form>

          </div>
        </div>

      </div>
    </div>
  );
}npm