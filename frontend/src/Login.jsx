import { useState } from "react";
import "./Login.css";

const API_URL = "http://localhost:8000";

function Login({ onLogin, initialMode = "login" }) {
  const [mode, setMode] = useState(initialMode);

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");
    setMessage("");

    if (!email.trim() || !password) {
      setError("Please enter your email and password.");
      return;
    }

    if (mode === "register" && !name.trim()) {
      setError("Please enter your name.");
      return;
    }

    setLoading(true);

    try {
      const endpoint =
        mode === "login"
          ? `${API_URL}/auth/login`
          : `${API_URL}/auth/register`;

      const body =
        mode === "login"
          ? {
              email: email.trim(),
              password,
            }
          : {
              name: name.trim(),
              email: email.trim(),
              password,
            };

      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Authentication failed."
        );
      }

      // ---------------------------------------------
      // REGISTER SUCCESS
      // ---------------------------------------------

      if (mode === "register") {
        setMode("login");
        setName("");
        setPassword("");

        setMessage(
          "Account created successfully. Please sign in."
        );

        return;
      }

      // ---------------------------------------------
      // LOGIN SUCCESS
      // ---------------------------------------------

      localStorage.setItem(
        "reqtrace_token",
        data.access_token
      );

      localStorage.setItem(
        "reqtrace_user",
        JSON.stringify(data.user)
      );

      setMessage("");

      if (onLogin) {
        onLogin(data.user);
      }

    } catch (err) {
      setError(
        err.message ||
          "Unable to connect to the backend."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <section
      className="login-wrapper"
      id="login"
    >
      <div className="login-card">

        <div className="login-label">
          {mode === "login"
            ? "WELCOME BACK"
            : "GET STARTED"}
        </div>

        <h2>
          {mode === "login"
            ? "Sign in."
            : "Create account."}
        </h2>

        <p className="login-description">
          {mode === "login"
            ? "Sign in to access your requirement workspace."
            : "Create your ReqTrace AI account."}
        </p>

        <form onSubmit={handleSubmit}>

          {mode === "register" && (
            <div className="login-field">
              <label>FULL NAME</label>

              <input
                type="text"
                placeholder="Your name"
                value={name}
                onChange={(event) =>
                  setName(event.target.value)
                }
              />
            </div>
          )}

          <div className="login-field">
            <label>EMAIL ADDRESS</label>

            <input
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(event) =>
                setEmail(event.target.value)
              }
            />
          </div>

          <div className="login-field">
            <label>PASSWORD</label>

            <input
              type="password"
              placeholder="Your password"
              value={password}
              onChange={(event) =>
                setPassword(event.target.value)
              }
            />
          </div>

          {error && (
            <div className="login-error">
              {error}
            </div>
          )}

          {message && (
            <div className="login-success">
              {message}
            </div>
          )}

          <button
            type="submit"
            className="login-button"
            disabled={loading}
          >
            <span>
              {loading
                ? "PLEASE WAIT..."
                : mode === "login"
                ? "SIGN IN"
                : "CREATE ACCOUNT"}
            </span>

            <span className="login-arrow">
              →
            </span>
          </button>

        </form>

        <div className="login-switch">

          <span>
            {mode === "login"
              ? "Don't have an account?"
              : "Already have an account?"}
          </span>

          <button
            type="button"
            onClick={() => {
              setMode(
                mode === "login"
                  ? "register"
                  : "login"
              );

              setError("");
              setMessage("");
            }}
          >
            {mode === "login"
              ? "Create account"
              : "Sign in"}
          </button>

        </div>

      </div>
    </section>
  );
}

export default Login;