import { useState, useEffect } from "react";
import "./KeyPopup.css";

function KeyPopup({ onSuccess }) {
  const [accessKey, setAccessKey] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const savedKey = localStorage.getItem("access_key");
    const savedDevice = localStorage.getItem("device_id");
    if (!savedKey || !savedDevice) return setLoading(false);

    fetch("http://localhost:8000/api/verify-key/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ key: savedKey, device_id: savedDevice }),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.valid) {
          onSuccess(savedKey, data.device_id);
        } else {
          localStorage.removeItem("access_key");
          localStorage.removeItem("device_id");
          setLoading(false);
        }
      })
      .catch(() => {
        setLoading(false);
      });
  }, []);

  const handleSubmit = async () => {
    setError("");
    const trimmedKey = accessKey.trim();
    if (!trimmedKey) {
      return setError("Please enter a key.");
    }

    try {
      const res = await fetch("http://localhost:8000/api/verify-key/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ key: trimmedKey }),
      });

      const data = await res.json();
      if (data.valid) {
        localStorage.setItem("access_key", trimmedKey);
        localStorage.setItem("device_id", data.device_id);
        onSuccess(trimmedKey, data.device_id);
      } else {
        setError(data.message || "Invalid key.");
      }
    } catch (err) {
      console.error(err);
      setError("Server error. Try again later.");
    }
  };

  if (loading) return null;

  return (
    <div id="blur-overlay">
      <div id="access-modal">
        <p id="modal-description">
          This page is protected. Please enter your access key to proceed.
          Each key is tied to device usage and may expire after set limits.
        </p>
        <input
          id="key-input"
          type="text"
          placeholder="Enter your access key here..."
          value={accessKey}
          onChange={(e) => setAccessKey(e.target.value)}
        />
        <button id="key-submit" onClick={handleSubmit}>Submit Key</button>
        {error && <div style={{ color: "#f88", marginTop: "1rem" }}>{error}</div>}
      </div>
    </div>
  );
}

export default KeyPopup;
