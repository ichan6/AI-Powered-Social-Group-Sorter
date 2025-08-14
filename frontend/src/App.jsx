// File: App.jsx (Refactored to enforce access key validation)
import { Routes, Route, Link, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import SortingPage from './pages/SortingPage.jsx';
import AboutPage from './pages/AboutPage.jsx';
import LandingPage from './pages/LandingPage.jsx';
import KeyPopup from './components/KeyPopup.jsx';
import './App.css';

function App() {
  const [isSorting, setIsSorting] = useState(false);
  const [keyValid, setKeyValid] = useState(false);
  const [checkingKey, setCheckingKey] = useState(true);
  const [deviceId, setDeviceId] = useState(null);

  useEffect(() => {
    const validateStoredKey = async () => {
      const storedKey = localStorage.getItem('access_key');
      const storedDevice = localStorage.getItem('device_id');
      if (!storedKey || !storedDevice) {
        setCheckingKey(false);
        return;
      }

      try {
        const res = await fetch('http://localhost:8000/api/validate-key/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ key: storedKey, device_id: storedDevice })
        });
        const data = await res.json();
        if (data.valid) {
          setKeyValid(true);
          setDeviceId(data.device_id);
        } else {
          localStorage.removeItem('access_key');
          localStorage.removeItem('device_id');
        }
      } catch (err) {
        console.error('Key validation failed:', err);
      }

      setCheckingKey(false);
    };

    validateStoredKey();
  }, []);

  const handleSuccessfulKey = (key, deviceId) => {
    localStorage.setItem('access_key', key);
    localStorage.setItem('device_id', deviceId);
    setDeviceId(deviceId);
    setKeyValid(true);
  };

  return (
    <>
      <nav id="navbar">
        <ul id="nav-links">
          <li><Link to="/" id="nav-landing" style={isSorting ? { pointerEvents: 'none', opacity: 0.5 } : {}}>Home</Link></li>
          <li><Link to="/sorting" id="nav-sort" style={isSorting ? { pointerEvents: 'none', opacity: 0.5 } : {}}>Sort</Link></li>
          <li><Link to="/about" id="nav-about" style={isSorting ? { pointerEvents: 'none', opacity: 0.5 } : {}}>About</Link></li>
        </ul>
      </nav>

      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route
          path="/sorting"
          element={
            keyValid ? (
              <SortingPage isSorting={isSorting} setIsSorting={setIsSorting} />
            ) : (
              <KeyPopup
                onSuccess={handleSuccessfulKey}
                checking={checkingKey}
              />
            )
          }
        />
        <Route path="/about" element={<AboutPage />} />
      </Routes>
    </>
  );
}

export default App;
