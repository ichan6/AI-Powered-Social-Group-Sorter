import { useEffect, useState } from 'react';
import KeyPopup from '../components/KeyPopup';
import './SortingPage.css';

function SortingPage({ isSorting, setIsSorting }) {
  const [progress, setProgress] = useState(0);
  const [progressMessage, setProgressMessage] = useState("Waiting to start...");
  const [file, setFile] = useState(null);
  const [textValue, setTextValue] = useState("");
  const [warningMessage, setWarningMessage] = useState("");
  const [accessGranted, setAccessGranted] = useState(false);

  useEffect(() => {
    const savedKey = localStorage.getItem("access_key");
    if (!savedKey) setAccessGranted(false);
    else setAccessGranted(true);
  }, []);

  const showSoftWarning = (message) => {
    setWarningMessage(message);
    setTimeout(() => setWarningMessage(""), 3000);
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && selectedFile.name.endsWith(".csv")) {
      setFile(selectedFile);
    } else {
      alert("Please upload a valid .csv file.");
      e.target.value = null;
    }
  };

  const handleSubmit = async () => {
    const key = localStorage.getItem("access_key");
    const deviceId = localStorage.getItem("device_id");

    const resValidate = await fetch("http://localhost:8000/api/validate-key/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ key, device_id: deviceId }),
    });

    const validationData = await resValidate.json();
    if (!validationData.valid) {
      alert(`Access denied: ${validationData.message || "Unknown error"}`);
      localStorage.removeItem("access_key");
      localStorage.removeItem("device_id");
      setAccessGranted(false);
      setIsSorting(false);
      return;
    }

    if (!file) {
      alert("Please upload a CSV file before submitting.");
      return;
    }

    setIsSorting(true);
    setProgress(1);
    setProgressMessage("Sorting Started! Please stay on this page!");

    const formData = new FormData();
    formData.append("file", file);
    formData.append("comments", textValue);

    const chaosMessages = [
      "Uploading CSV to NASA mainframe...",
      "Negotiating with the data overlords...",
      "Distributing energy crystals...",
      "Converting personalities to vectors...",
      "Tuning the vibe algorithm 🔮...",
      "Summoning social chemistry gods...",
      "Balancing chaos & friendship...",
      "Measuring introvert–extrovert force fields...",
      "Hacking Hogwarts Sorting Hat...",
      "Analyzing vibe clusters...",
      "Assembling friend-shaped families...",
      "Spinning up cosmic compatibility checks...",
      "Waiting for the stars to align...",
      "Consulting personality horoscopes...",
      "Rearranging vibes like LEGO bricks...",
      "Defragmenting human souls...",
      "Inferring social gravitation wells...",
      "Compiling new friend ecosystems...",
      "Adjusting resonance frequencies...",
      "Reconstructing friendships from pixels..."
    ];

    const shuffledMessages = chaosMessages
      .map(msg => ({ msg, sort: Math.random() }))
      .sort((a, b) => a.sort - b.sort)
      .map(obj => obj.msg);

    let progress = 0;
    let msgIndex = 0;

    const intervalDuration = 15000;
    const progressIncrement = 90 / shuffledMessages.length;

    const stageInterval = setInterval(() => {
      if (progress >= 90 || msgIndex >= shuffledMessages.length) return;

      progress = Math.min(progress + progressIncrement, 90);
      const nextMessage = shuffledMessages[msgIndex++ % shuffledMessages.length];
      setProgress(progress);
      setProgressMessage(nextMessage);
    }, intervalDuration);

    try {
      const res = await fetch("http://localhost:8000/api/sort/", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) throw new Error("Failed to sort.");

      const blob = await res.blob();

      clearInterval(stageInterval);
      setProgress(100);
      setProgressMessage("Sorting complete! File downloaded.");

      setIsSorting(false);

      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "sorted_families.csv";
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      clearInterval(stageInterval);
      console.error(err);
      setProgress(0);
      setProgressMessage("Something went wrong during sorting 😵‍💫");
      setIsSorting(false);
    }
  };

  return (
    <div id="app-container">
      {!accessGranted && (
        <KeyPopup onSuccess={() => setAccessGranted(true)} />
      )}

      {accessGranted && (
        <div id="content-wrapper">
          <h1 id="main-title">Family Sorting Application</h1>

          <textarea
            id="text-input"
            placeholder="e.g., Try to group based on music taste and personality. Split large friend groups if possible."
            value={textValue}
            onChange={(e) => {
              if (isSorting) {
                showSoftWarning("Sorting is in progress — you can't edit instructions.");
              } else {
                setTextValue(e.target.value);
              }
            }}
            disabled={isSorting}
            style={isSorting ? { opacity: 0.6, cursor: "not-allowed" } : {}}
          />

          <div id="file-upload-section">
            <label htmlFor="csv-upload" id="upload-label">Upload CSV File:</label>
            <input
              type="file"
              id="csv-upload"
              accept=".csv"
              onChange={(e) => {
                if (isSorting) {
                  showSoftWarning("Sorting is in progress — file upload disabled.");
                } else {
                  handleFileChange(e);
                }
              }}
              disabled={isSorting}
              style={isSorting ? { opacity: 0.6, cursor: "not-allowed" } : {}}
            />
          </div>

          <button
            id="submit-button"
            onClick={handleSubmit}
            disabled={isSorting}
            style={isSorting ? { opacity: 0.6, cursor: "not-allowed" } : {}}
          >
            Submit for Sorting
          </button>

          {warningMessage && <div id="soft-warning">{warningMessage}</div>}

          <div id="progress-container">
            <div id="progress-bar" style={{ width: `${progress}%` }}>
              <span id="progress-text">{progressMessage}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default SortingPage;
