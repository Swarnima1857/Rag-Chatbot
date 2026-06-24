import { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

export default function Signup() {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSignup = async () => {
      if (!username || !email || !password) {
        alert("Please fill all fields!");
        return;
      }
      try {
        setLoading(true);
        const response = await axios.post(
          "http://127.0.0.1:8000/auth/signup",
          { username, email, password }
        );
        alert("Account created successfully! Please login.");
      navigate("/");
    } catch (error) {
      alert("Signup failed! Email already exists.");
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

      {/* Left Side — Illustration */}
      <div style={{
        flex: 1,
        background: "linear-gradient(135deg, #f97316, #ef4444)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "40px",
        color: "white"
      }}>
        <div style={{ fontSize: "120px", marginBottom: "24px" }}>🤖</div>

        <h2 style={{ fontSize: "28px", fontWeight: "bold", margin: "0 0 12px" }}>
          Join RAG Chatbot!
        </h2>
        <p style={{ fontSize: "16px", opacity: 0.9, textAlign: "center", maxWidth: "280px" }}>
          Create your account and start chatting with your documents!
        </p>

        <div style={{ marginTop: "40px", display: "flex", flexDirection: "column", gap: "16px" }}>
          {[
            { icon: "🚀", text: "Get started in seconds" },
            { icon: "🔒", text: "Your data is secure" },
            { icon: "📂", text: "Multiple chat sessions" },
            { icon: "🤖", text: "Powered by local AI" },
          ].map((item, i) => (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: "12px" }}>
              <span style={{ fontSize: "20px" }}>{item.icon}</span>
              <span style={{ fontSize: "15px", opacity: 0.9 }}>{item.text}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Right Side — Signup Form */}
      <div style={{
        flex: 1,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "40px"
      }}>
        <div style={{ width: "100%", maxWidth: "400px" }}>

          <h1 style={{ fontSize: "28px", fontWeight: "bold", color: "#0f172a", marginBottom: "8px" }}>
            Create Account 🎉
          </h1>
          <p style={{ color: "#6b7280", marginBottom: "32px" }}>
            Sign up to get started!
          </p>

          {/* Username */}
          <div style={{ marginBottom: "20px" }}>
            <label style={{ fontSize: "14px", fontWeight: "500", color: "#374151", display: "block", marginBottom: "6px" }}>
              Username
            </label>
            <input
              type="text"
              placeholder="Your name"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              style={{
                width: "100%", padding: "12px 16px",
                border: "2px solid #e5e7eb", borderRadius: "10px",
                fontSize: "14px", outline: "none",
                boxSizing: "border-box", background: "white"
              }}
              onFocus={(e) => e.target.style.borderColor = "#f97316"}
              onBlur={(e) => e.target.style.borderColor = "#e5e7eb"}
            />
          </div>

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
              onFocus={(e) => e.target.style.borderColor = "#f97316"}
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
              placeholder="Create a password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={{
                width: "100%", padding: "12px 16px",
                border: "2px solid #e5e7eb", borderRadius: "10px",
                fontSize: "14px", outline: "none",
                boxSizing: "border-box", background: "white"
              }}
              onFocus={(e) => e.target.style.borderColor = "#f97316"}
              onBlur={(e) => e.target.style.borderColor = "#e5e7eb"}
            />
          </div>

          {/* Signup Button */}
          <button
            onClick={handleSignup}
            disabled={loading}
            style={{
              width: "100%", padding: "14px",
              background: "linear-gradient(135deg, #f97316, #ef4444)",
              color: "white", border: "none", borderRadius: "10px",
              fontSize: "16px", fontWeight: "600", cursor: "pointer",
              boxShadow: "0 4px 15px rgba(249, 115, 22, 0.4)"
            }}
            onMouseOver={(e) => e.target.style.opacity = "0.9"}
            onMouseOut={(e) => e.target.style.opacity = "1"}
          >
            Create Account →
          </button>

          <p style={{ textAlign: "center", marginTop: "24px", color: "#6b7280", fontSize: "14px" }}>
            Already have an account?{" "}
            <span
              onClick={() => navigate("/")}
              style={{ color: "#f97316", fontWeight: "600", cursor: "pointer" }}
            >
              Login
            </span>
          </p>

        </div>
      </div>

    </div>
  );
}