import { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async () => {
    if (!email || !password) {
      alert("Please fill all fields!");
      return;
    }
    try {
      setLoading(true);
      const response = await axios.post(
        "http://127.0.0.1:8000/auth/login",
        { email, password }
      );
      localStorage.setItem("token", response.data.access_token);
      navigate("/chat");
    } catch (error) {
      alert("Login failed! Check email and password.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: "100vh",
      display: "flex",
      fontFamily: "'Segoe UI', sans-serif",
      background: "#f0fafa"
    }}>

      {/* Left Side */}
      <div style={{
        flex: 1,
        background: "linear-gradient(135deg, #0d9488, #0891b2)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "40px",
        color: "white"
      }}>
        <div style={{ fontSize: "120px", marginBottom: "24px" }}>🤖</div>
        <h2 style={{ fontSize: "28px", fontWeight: "bold", margin: "0 0 12px" }}>
          RAG Chatbot
        </h2>
        <p style={{ fontSize: "16px", opacity: 0.9, textAlign: "center", maxWidth: "280px" }}>
          Upload your documents and chat with AI!
        </p>
        <div style={{ marginTop: "40px", display: "flex", flexDirection: "column", gap: "16px" }}>
          {[
            { icon: "📄", text: "Upload PDF documents" },
            { icon: "🔍", text: "Smart semantic search" },
            { icon: "💬", text: "AI powered answers" },
            { icon: "📚", text: "Save chat history" },
          ].map((item, i) => (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: "12px" }}>
              <span style={{ fontSize: "20px" }}>{item.icon}</span>
              <span style={{ fontSize: "15px", opacity: 0.9 }}>{item.text}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Right Side */}
      <div style={{
        flex: 1,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "40px"
      }}>
        <div style={{ width: "100%", maxWidth: "400px" }}>
          <h1 style={{ fontSize: "28px", fontWeight: "bold", color: "#0f172a", marginBottom: "8px" }}>
            Welcome Back! 👋
          </h1>
          <p style={{ color: "#6b7280", marginBottom: "32px" }}>
            Login to continue to RAG Chatbot
          </p>

          {/* Email */}
          <div style={{ marginBottom: "20px" }}>
            <label style={{ fontSize: "14px", fontWeight: "500", color: "#374151", display: "block", marginBottom: "6px" }}>
              Email Address
            </label>
            <input
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              style={{
                width: "100%", padding: "12px 16px",
                border: "2px solid #e5e7eb", borderRadius: "10px",
                fontSize: "14px", outline: "none",
                boxSizing: "border-box", background: "white"
              }}
              onFocus={(e) => e.target.style.borderColor = "#0d9488"}
              onBlur={(e) => e.target.style.borderColor = "#e5e7eb"}
            />
          </div>

          {/* Password */}
          <div style={{ marginBottom: "28px" }}>
            <label style={{ fontSize: "14px", fontWeight: "500", color: "#374151", display: "block", marginBottom: "6px" }}>
              Password
            </label>
            <input
              type="password"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={{
                width: "100%", padding: "12px 16px",
                border: "2px solid #e5e7eb", borderRadius: "10px",
                fontSize: "14px", outline: "none",
                boxSizing: "border-box", background: "white"
              }}
              onFocus={(e) => e.target.style.borderColor = "#0d9488"}
              onBlur={(e) => e.target.style.borderColor = "#e5e7eb"}
            />
          </div>

          {/* Button */}
          <button
            onClick={handleLogin}
            disabled={loading}
            style={{
              width: "100%", padding: "14px",
              background: loading ? "#9ca3af" : "linear-gradient(135deg, #0d9488, #0891b2)",
              color: "white", border: "none", borderRadius: "10px",
              fontSize: "16px", fontWeight: "600", cursor: loading ? "not-allowed" : "pointer",
              boxShadow: "0 4px 15px rgba(13, 148, 136, 0.4)"
            }}
          >
            {loading ? "Logging in..." : "Login →"}
          </button>

          <p style={{ textAlign: "center", marginTop: "24px", color: "#6b7280", fontSize: "14px" }}>
            Don't have an account?{" "}
            <span
              onClick={() => navigate("/signup")}
              style={{ color: "#0d9488", fontWeight: "600", cursor: "pointer" }}
            >
              Sign Up
            </span>
          </p>
        </div>
      </div>
    </div>
  );
}