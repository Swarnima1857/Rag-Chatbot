import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

export default function Chat() {
  const navigate = useNavigate();

  // ===== STATE VARIABLES =====
  // Sare sessions ki list
  const [sessions, setSessions] = useState([]);
  // Abhi kaunsa session khula hai
  const [activeSession, setActiveSession] = useState(null);
  // Chat messages (questions + answers)
  const [messages, setMessages] = useState([]);
  // Input box mein jo type ho raha hai
  const [question, setQuestion] = useState("");
  // PDF upload hua ya nahi (kitne chunks bane)
  const [pdfInfo, setPdfInfo] = useState(null);
  // Loading states
  const [isAsking, setIsAsking] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  // Scroll ke liye reference (naya message aane pe neeche scroll ho)
  const messagesEndRef = useRef(null);

  // Token nikal lo localStorage se
  const token = localStorage.getItem("token");

  // Axios ke liye common headers (har request mein token jayega)
  const authHeaders = {
    headers: { Authorization: `Bearer ${token}` }
  };

  // ===== PAGE LOAD HONE PE — SESSIONS LAO =====
  useEffect(() => {
    if (!token) {
      // Agar token nahi hai, login page pe bhejo
      navigate("/");
      return;
    }
    fetchSessions();
  }, []);

  // ===== NAYA MESSAGE AANE PE NEECHE SCROLL KARO =====
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // ===== FUNCTION: Sare sessions fetch karo =====
  const fetchSessions = async () => {
    try {
      const response = await axios.get(
        "http://127.0.0.1:8000/sessions/all",
        authHeaders
      );
      setSessions(response.data);
    } catch (error) {
      console.log("Error fetching sessions:", error);
    }
  };

  // ===== FUNCTION: Naya session banao =====
  const createNewSession = async () => {
    try {
      const response = await axios.post(
        "http://127.0.0.1:8000/sessions/create",
        { title: "New Chat" },
        authHeaders
      );
      // Naya session list mein add karo
      setSessions([...sessions, response.data]);
      // Use turant select kar do
      selectSession(response.data.session_id);
    } catch (error) {
      alert("Failed to create session");
    }
  };

  // ===== FUNCTION: Session select karo (click karne pe) =====
  const selectSession = async (sessionId) => {
    setActiveSession(sessionId);
    setMessages([]);
    setPdfInfo(null);
    // Us session ki purani history load karo
    try {
      const response = await axios.get(
        `http://127.0.0.1:8000/chat/history/${sessionId}`,
        authHeaders
      );
      setMessages(response.data);
    } catch (error) {
      console.log("No history found");
    }
  };

  // ===== FUNCTION: PDF Upload karo =====
  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file || !activeSession) return;

    // FormData banana padta hai file bhejne ke liye
    const formData = new FormData();
    formData.append("file", file);

    try {
      setIsUploading(true);
      const response = await axios.post(
        `http://127.0.0.1:8000/chat/upload/${activeSession}`,
        formData,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "multipart/form-data"
          }
        }
      );
      setPdfInfo({ name: file.name, chunks: response.data.chunks_created });
    } catch (error) {
      alert("PDF upload failed!");
    } finally {
      setIsUploading(false);
    }
  };

  // ===== FUNCTION: Sawaal poochho =====
  const handleAskQuestion = async () => {
    if (!question.trim() || !activeSession) return;

    // User ka message turant dikhao (optimistic update)
    const userMessage = { question, answer: null };
    setMessages((prev) => [...prev, userMessage]);
    setQuestion("");

    try {
      setIsAsking(true);
      const response = await axios.post(
        "http://127.0.0.1:8000/chat/ask",
        { session_id: activeSession, question },
        authHeaders
      );
      // Jawab aane pe last message update karo
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1].answer = response.data.answer;
        return updated;
      });
    } catch (error) {
      alert("Failed to get answer!");
    } finally {
      setIsAsking(false);
    }
  };

  // ===== FUNCTION: Logout =====
  const handleLogout = () => {
    localStorage.removeItem("token");
    navigate("/");
  };

  // ===== UI START =====
  return (
    <div style={{
      height: "100vh",
      display: "flex",
      fontFamily: "'Segoe UI', sans-serif",
      background: "#f0fafa"
    }}>

      {/* ============ SIDEBAR ============ */}
      <div style={{
        width: "260px",
        background: "white",
        borderRight: "1px solid #e5e7eb",
        padding: "16px",
        display: "flex",
        flexDirection: "column",
        gap: "8px"
      }}>

        {/* New Chat Button */}
        <button
          onClick={createNewSession}
          style={{
            background: "linear-gradient(135deg, #0d9488, #0891b2)",
            border: "none", color: "white", fontWeight: "600",
            fontSize: "14px", padding: "12px", borderRadius: "10px",
            cursor: "pointer"
          }}
        >
          + New Chat
        </button>

        <p style={{ fontSize: "11px", color: "#6b7280", fontWeight: "600", marginTop: "16px", marginBottom: "4px", textTransform: "uppercase" }}>
          Sessions
        </p>

        {/* Sessions List */}
        <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: "4px" }}>
          {sessions.map((session) => (
            <div
              key={session.session_id}
              onClick={() => selectSession(session.session_id)}
              style={{
                padding: "10px",
                borderRadius: "8px",
                fontSize: "13px",
                cursor: "pointer",
                background: activeSession === session.session_id ? "#e1f5ee" : "transparent",
                color: activeSession === session.session_id ? "#085041" : "#374151",
                fontWeight: activeSession === session.session_id ? "600" : "400"
              }}
            >
              💬 {session.title}
            </div>
          ))}
        </div>

        {/* User Info + Logout */}
        <div style={{
          borderTop: "1px solid #e5e7eb", paddingTop: "14px",
          display: "flex", alignItems: "center", gap: "8px"
        }}>
          <div style={{
            width: "30px", height: "30px", borderRadius: "50%",
            background: "linear-gradient(135deg, #0d9488, #f97316)",
            display: "flex", alignItems: "center", justifyContent: "center",
            color: "white", fontSize: "12px", fontWeight: "600"
          }}>
            S
          </div>
          <span style={{ flex: 1, fontSize: "13px", color: "#374151" }}>
            My Account
          </span>
          <span onClick={handleLogout} style={{ cursor: "pointer", fontSize: "13px", color: "#ef4444" }}>
            Logout
          </span>
        </div>
      </div>

      {/* ============ MAIN CHAT AREA ============ */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>

        {!activeSession ? (
          // Agar koi session select nahi hai
          <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", color: "#9ca3af" }}>
            <p>👈 Select or create a chat session to start</p>
          </div>
        ) : (
          <>
            {/* Header — PDF info */}
            <div style={{
              padding: "14px 20px", borderBottom: "1px solid #e5e7eb",
              display: "flex", alignItems: "center", justifyContent: "space-between"
            }}>
              <span style={{ fontWeight: "600", fontSize: "14px" }}>
                {pdfInfo ? `📄 ${pdfInfo.name}` : "No PDF uploaded yet"}
              </span>
              {pdfInfo && (
                <span style={{
                  fontSize: "12px", color: "#085041", background: "#e1f5ee",
                  padding: "4px 10px", borderRadius: "12px"
                }}>
                  ✅ {pdfInfo.chunks} chunks ready
                </span>
              )}
            </div>

            {/* Messages Area */}
            <div style={{ flex: 1, padding: "20px", overflowY: "auto", background: "#fafafa" }}>
              {messages.map((msg, i) => (
                <div key={i} style={{ marginBottom: "16px" }}>
                  {/* User question — right side */}
                  <div style={{
                    alignSelf: "flex-end", maxWidth: "70%", marginLeft: "auto",
                    background: "linear-gradient(135deg, #0d9488, #0891b2)",
                    color: "white", padding: "10px 14px",
                    borderRadius: "14px 14px 4px 14px", fontSize: "14px",
                    marginBottom: "8px", width: "fit-content"
                  }}>
                    {msg.question}
                  </div>

                  {/* AI answer — left side */}
                  {msg.answer ? (
                    <div style={{
                      maxWidth: "70%", background: "white", border: "1px solid #e5e7eb",
                      padding: "10px 14px", borderRadius: "14px 14px 14px 4px",
                      fontSize: "14px", color: "#1f2937"
                    }}>
                      {msg.answer}
                    </div>
                  ) : (
                    <div style={{ fontSize: "13px", color: "#9ca3af" }}>
                      AI is thinking...
                    </div>
                  )}
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div style={{
              padding: "14px 20px", borderTop: "1px solid #e5e7eb",
              display: "flex", gap: "10px", alignItems: "center", background: "white"
            }}>
              {/* PDF Upload Button */}
              <label style={{
                width: "36px", height: "36px", borderRadius: "10px",
                background: "#f3f4f6", display: "flex", alignItems: "center",
                justifyContent: "center", cursor: "pointer", flexShrink: 0
              }}>
                📎
                <input
                  type="file"
                  accept=".pdf"
                  onChange={handleFileUpload}
                  style={{ display: "none" }}
                />
              </label>

              {/* Text Input */}
              <input
                type="text"
                placeholder={isUploading ? "Uploading PDF..." : "Ask something about your PDF..."}
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleAskQuestion()}
                disabled={isUploading}
                style={{
                  flex: 1, borderRadius: "20px", border: "1px solid #e5e7eb",
                  padding: "10px 16px", fontSize: "14px", outline: "none"
                }}
              />

              {/* Send Button */}
              <button
                onClick={handleAskQuestion}
                disabled={isAsking}
                style={{
                  width: "36px", height: "36px", borderRadius: "50%",
                  background: "linear-gradient(135deg, #0d9488, #0891b2)",
                  border: "none", color: "white", cursor: "pointer", flexShrink: 0
                }}
              >
                ➤
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}