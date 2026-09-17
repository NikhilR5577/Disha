import SearchableDropdown from './components/SearchableDropdown';
import { useState, useEffect, useRef } from 'react'
import HospitalMap from './components/HospitalMap'
import { Mic, QrCode, X, Moon, Sun, AlertTriangle, BarChart2, Share2 } from 'lucide-react'
import { Scanner } from '@yudiel/react-qr-scanner'
import './App.css'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

function App() {
  const [locations, setLocations] = useState([]);
  const [start, setStart] = useState('');
  const [destination, setDestination] = useState('');
  const [route, setRoute] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [currentFloor, setCurrentFloor] = useState(1);
  const [language, setLanguage] = useState('en'); // 'en' or 'hi'
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isAccessible, setIsAccessible] = useState(false);
  const [autoAudio, setAutoAudio] = useState(true);
  
  // Voice Input State
  const [isListening, setIsListening] = useState(false);
  const [voiceTriggerNavigate, setVoiceTriggerNavigate] = useState(false);
  
  // URL Share State
  const [highlightStart, setHighlightStart] = useState(false);
  const [heardText, setHeardText] = useState('');

  // QR Scanner State
  const [showQRScanner, setShowQRScanner] = useState(false);

  // Stats State
  const [showStats, setShowStats] = useState(false);
  const [statsData, setStatsData] = useState(null);

  const handleOpenStats = async () => {
    setShowStats(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/analytics/stats`);
      const data = await res.json();
      setStatsData(data);
    } catch (err) {
      console.error('Failed to load stats', err);
    }
  };

  // Advanced Features State
  const [isDarkMode, setIsDarkMode] = useState(() => { const h = new Date().getHours(); return h >= 19 || h < 7; });
  const [isInitialLoading, setIsInitialLoading] = useState(true);

  useEffect(() => {
    // Generate or get a unique session ID for the user
    let sessionId = localStorage.getItem('disha_session_id');
    if (!sessionId) {
        sessionId = 'sess_' + Math.random().toString(36).substr(2, 9) + Date.now();
        localStorage.setItem('disha_session_id', sessionId);
    }

    // Track app open
    fetch(`${API_BASE_URL}/api/analytics/track`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            event_type: 'app_opened',
            session_id: sessionId
        })
    }).catch(err => console.error('Analytics error:', err));
  }, []);

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/locations`)
      .then(res => res.json())
      .then(data => {
        // Filter out waypoints from dropdowns
        const displayLocations = data.filter(loc => loc.is_room === true || loc.is_room === 1);
        setLocations(displayLocations);
        
        // URL Integration (?start= and ?dest=)
        const urlParams = new URLSearchParams(window.location.search);
        const startParam = urlParams.get('start');
        const destParam = urlParams.get('dest');
        
        let hasSetStart = false;
        let hasSetDest = false;

        // 1. Handle Destination (from Shared Links)
        if (destParam && displayLocations.some(loc => loc.id === destParam)) {
          setDestination(destParam);
          hasSetDest = true;
          // If they only have a destination, leave Start empty so they scan a QR!
          setStart('');
          hasSetStart = true; // explicitly left blank
          if (!startParam) {
            setHighlightStart(true);
          }
        }

        // 2. Handle Start (from QR Codes)
        if (startParam && displayLocations.some(loc => loc.id === startParam)) {
          setStart(startParam);
          hasSetStart = true;
          if (!hasSetDest) {
            const otherLocs = displayLocations.filter(loc => loc.id !== startParam);
            if (otherLocs.length > 0) {
              setDestination(otherLocs[0].id);
              hasSetDest = true;
            }
          }
        }

        // 3. Fallbacks if normal launch
        if (!hasSetStart && displayLocations.length > 0) {
          const mainEntrance = displayLocations.find(loc => loc.id === 'd_main_entrance');
          if (mainEntrance) {
            setStart(mainEntrance.id);
          } else {
            setStart(displayLocations[0].id);
          }
        }

        if (!hasSetDest && displayLocations.length > 1) {
          const mainEntranceId = displayLocations.find(loc => loc.id === 'd_main_entrance')?.id;
          const otherLocs = displayLocations.filter(loc => loc.id !== mainEntranceId);
          setDestination(otherLocs.length > 0 ? otherLocs[0].id : displayLocations[1].id);
        }

        // 4. Auto-route if both are valid in URL
        if (startParam && destParam) {
           setTimeout(() => setVoiceTriggerNavigate(true), 500); // reuse voice trigger to auto-navigate
        }
      })
      .catch(err => console.error("Error fetching locations", err))
      .finally(() => setIsInitialLoading(false));
  }, []);

  // Effect to auto-trigger navigation when voice sets a destination
  useEffect(() => {
    if (voiceTriggerNavigate && start && destination && start !== destination) {
      setVoiceTriggerNavigate(false);
      handleNavigate();
    }
  }, [destination, voiceTriggerNavigate, start]);

  const handleNavigate = async (overrideStart = start, overrideDest = destination) => {
    setLoading(true);
    setError('');
    setRoute(null);
    stopSpeaking();
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/route?start=${overrideStart}&destination=${overrideDest}&accessible=${isAccessible}`);
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to fetch route');
      }
      if (!data.path_found) {
        throw new Error(language === 'hi' ? 'कोई रास्ता नहीं मिला। (क्या आप बिना लिफ्ट के फर्श पार करने की कोशिश कर रहे हैं?)' : 'No route found. (Are you trying to cross floors without a lift?)');
      }
      
      setRoute(data);
      // Automatically switch to the floor where the route starts
      if (data.steps && data.steps.length > 0) {
        setCurrentFloor(data.steps[0].floor);
      }
      
      if (autoAudio) {
        // Need to wait slightly for state to settle, or pass data directly
        setTimeout(() => speakRouteData(data), 100);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleShare = async () => {
    if (!start) {
      alert(language === 'hi' ? 'लिंक शेयर करने से पहले कृपया अपना वर्तमान स्थान चुनें!' : 'Please select your Current Location first to share it!');
      return;
    }
    
    const destName = locations.find(l => l.id === start)?.name || 'Destination';
    const destNameHi = locations.find(l => l.id === start)?.name_hi || destName;
    
    // Confirmation popup to re-check location before sharing
    const confirmMsg = language === 'hi'
      ? `क्या आप सही में "${destNameHi}" पर हैं?\n\nयह लोकेशन शेयर होगी।`
      : `Are you sure you are at "${destName}"?\n\nThis location will be shared.`;
    
    if (!confirm(confirmMsg)) return;
    
    const shareUrl = `${window.location.origin}${window.location.pathname}?dest=${start}`;
    
    const shareData = {
      title: 'Disha - Hospital Navigation',
      text: language === 'hi' 
        ? `मैं यहाँ हूँ! मुझसे ${destNameHi} पर मिलें। यहाँ क्लिक करें:` 
        : `Meet me at ${destName}. Click here for walking directions:`,
      url: shareUrl
    };

    try {
      if (navigator.share) {
        await navigator.share(shareData);
      } else {
        await navigator.clipboard.writeText(`${shareData.text} ${shareData.url}`);
        alert(language === 'hi' ? 'लिंक कॉपी हो गया!' : 'Link copied to clipboard!');
      }
    } catch (err) {
      console.error('Error sharing:', err);
    }
  };

  const getFloorName = (floorNum) => {
    if (language === 'hi') return floorNum === 1 ? 'ग्राउंड फ्लोर' : 'प्रथम तल';
    return floorNum === 1 ? 'Ground Floor' : 'First Floor';
  };

  const speakRouteData = (routeData) => {
    if (isSpeaking) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      return;
    }

    if (!routeData || !routeData.path_found) return;

    let fullText = language === 'hi' 
      ? `कुल दूरी ${Math.round(routeData.total_distance)} यूनिट है। ` 
      : `Total distance is ${Math.round(routeData.total_distance)} units. `;
    
    routeData.steps.forEach((step, idx) => {
      const instruction = language === 'hi' ? step.instruction_hi : step.instruction_en;
      fullText += `${language === 'hi' ? 'कदम' : 'Step'} ${idx + 1}: ${instruction}. `;
    });

    const utterance = new SpeechSynthesisUtterance(fullText);
    utterance.lang = language === 'hi' ? 'hi-IN' : 'en-US';
    utterance.rate = 0.9;
    
    utterance.onend = () => setIsSpeaking(false);
    
    window.speechSynthesis.speak(utterance);
    setIsSpeaking(true);
  };

  const speakRoute = () => {
    speakRouteData(route);
  };

  const stopSpeaking = () => {
    window.speechSynthesis.cancel();
    setIsSpeaking(false);
  };

  const handleEmergency = () => {
    if (!start) {
      alert(language === 'hi' ? "कृपया पहले अपना वर्तमान स्थान चुनें" : "Please select your location first");
      return;
    }
    setDestination('r6');
    setTimeout(() => handleNavigate(start, 'r6'), 100);
  };

  const [qrScanStatus, setQrScanStatus] = useState('');

  const handleQRScan = (detectedCodes) => {
    console.log("QR onScan fired:", detectedCodes);

    let text = '';
    if (Array.isArray(detectedCodes) && detectedCodes.length > 0) {
      text = detectedCodes[0].rawValue;
    } else if (typeof detectedCodes === 'string') {
      text = detectedCodes;
    }

    if (!text) return;
    
    console.log("QR scanned text:", text);
    setQrScanStatus(`Scanned: ${text.substring(0, 60)}...`);

    if (text.includes('?start=')) {
      try {
        const url = new URL(text);
        const startParam = url.searchParams.get('start');
        if (startParam && locations.some(loc => loc.id === startParam)) {
          setStart(startParam);
          setShowQRScanner(false);
          setQrScanStatus('');
        } else {
          setQrScanStatus(`Location "${startParam}" not found in system.`);
        }
      } catch (err) {
        console.error("Invalid URL in QR code:", text);
        setQrScanStatus('Invalid QR code URL format.');
      }
    } else {
      // Try matching the raw text as a location ID directly
      const matchedLoc = locations.find(loc => loc.id === text || loc.name.toLowerCase() === text.toLowerCase());
      if (matchedLoc) {
        setStart(matchedLoc.id);
        setShowQRScanner(false);
        setQrScanStatus('');
      } else {
        setQrScanStatus(`QR code read, but not a Disha code.`);
      }
    }
  }

  const toggleQRScanner = () => {
    setShowQRScanner(!showQRScanner);
  }

  // Voice Input Implementation
  const heardTextRef = useRef(''); // Use ref to avoid stale closure in recognition.onend
  const startListening = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert(language === 'hi' ? "आपका ब्राउज़र वॉयस इनपुट का समर्थन नहीं करता। कृपया Chrome का उपयोग करें।" : "Your browser does not support voice input. Please use Chrome.");
      return;
    }
    
    const recognition = new SpeechRecognition();
    recognition.lang = language === 'hi' ? 'hi-IN' : 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognition.continuous = false;

    setIsListening(true);
    heardTextRef.current = 'Listening...';
    setHeardText('Listening...');
    stopSpeaking();

    recognition.onresult = async (event) => {
      const speechResult = event.results[0][0].transcript.toLowerCase().trim();
      console.log("Heard:", speechResult);
      heardTextRef.current = `Heard: "${speechResult}"`;
      setHeardText(`Heard: "${speechResult}"`);
      
      try {
        const response = await fetch(`${API_BASE_URL}/api/search?q=${encodeURIComponent(speechResult)}`);
        const match = await response.json();
        
        if (match && match.id) {
          setDestination(match.id);
          setTimeout(() => setVoiceTriggerNavigate(true), 100);
        } else {
          heardTextRef.current = `No match for: "${speechResult}"`;
          setTimeout(() => setHeardText(`No match for: "${speechResult}"`), 500);
        }
      } catch (e) {
        console.error("Search error:", e);
        heardTextRef.current = "Error searching";
        setHeardText("Error searching");
      }
    };

    recognition.onend = () => {
      setIsListening(false);
      if (heardTextRef.current === 'Listening...') {
        heardTextRef.current = '';
        setHeardText('');
      }
    };

    recognition.onerror = (event) => {
      console.error("Speech recognition error", event.error);
      setIsListening(false);
      const errorMessages = {
        'no-speech': language === 'hi' ? 'कोई आवाज़ नहीं सुनाई दी। दोबारा कोशिश करें।' : 'No speech detected. Try again.',
        'not-allowed': language === 'hi' ? 'माइक्रोफ़ोन की अनुमति दें और दोबारा कोशिश करें।' : 'Microphone permission denied. Please allow access.',
        'network': language === 'hi' ? 'नेटवर्क त्रुटि। इंटरनेट कनेक्शन जांचें।' : 'Network error. Check your internet connection.',
        'aborted': '',
      };
      const msg = errorMessages[event.error] ?? `Error: ${event.error}`;
      heardTextRef.current = msg;
      setHeardText(msg);
    };

    try {
      recognition.start();
    } catch (e) {
      console.error("Could not start recognition:", e);
      setIsListening(false);
      setHeardText(language === 'hi' ? 'माइक शुरू नहीं हो सका।' : 'Could not start microphone.');
    }
  };

  if (isInitialLoading) {
    return (
      <div className={`min-h-[100dvh] flex flex-col items-center justify-center transition-colors ${isDarkMode ? 'bg-gray-900 text-white' : 'bg-orange-500 text-white'}`}>
        <div className={`w-20 h-20 rounded-2xl flex items-center justify-center shadow-xl animate-pulse mb-6 ${isDarkMode ? 'bg-gray-800' : 'bg-white'}`}>
          <svg className={`w-12 h-12 ${isDarkMode ? 'text-orange-300' : 'text-orange-500'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" />
          </svg>
        </div>
        <h1 className="text-3xl font-black tracking-tight mb-2">Disha</h1>
        <p className="text-sm font-semibold opacity-80 uppercase tracking-widest">{language === 'hi' ? 'Powered by AWS Cloud' : 'Powered by AWS Cloud'}</p>
        <div className="mt-8 flex gap-2">
          <div className="w-2 h-2 rounded-full bg-white opacity-80 animate-bounce" style={{ animationDelay: '0ms' }}></div>
          <div className="w-2 h-2 rounded-full bg-white opacity-80 animate-bounce" style={{ animationDelay: '150ms' }}></div>
          <div className="w-2 h-2 rounded-full bg-white opacity-80 animate-bounce" style={{ animationDelay: '300ms' }}></div>
        </div>
      </div>
    );
  }

  return (
    <div className={`min-h-[100dvh] text-gray-800 font-sans flex flex-col relative overflow-hidden transition-colors duration-300 ${isDarkMode ? 'dark bg-gray-900' : 'bg-[#F0F4F8]'}`}>
        
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 p-4 sm:p-5 shadow-sm z-10 shrink-0 flex justify-between items-center w-full transition-colors duration-300">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-orange-500 dark:bg-orange-400 rounded-xl flex items-center justify-center shadow-md">
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" />
            </svg>
          </div>
          <div>
            <h1 className="text-xl sm:text-2xl font-black text-gray-900 dark:text-white tracking-tight leading-none mb-1 transition-colors">Disha</h1>
            <p className="text-[10px] sm:text-xs font-bold text-orange-500 dark:text-orange-300 uppercase tracking-wider transition-colors">{language === 'hi' ? 'Powered by AWS Cloud' : 'Powered by AWS Cloud'}</p>
          </div>
        </div>
                  <div className="flex items-center gap-2 lg:gap-3 shrink-0">
            <button onClick={() => setIsDarkMode(!isDarkMode)} className="p-2 text-gray-500 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full transition-colors" title={isDarkMode ? "Light Mode" : "Dark Mode"}>{isDarkMode ? <Sun size={20} /> : <Moon size={20} />}</button>
        </div>
      </header>

      {/* Main Content Layout */}
      <div className="flex flex-col lg:flex-row flex-grow overflow-hidden relative max-w-[1600px] w-full mx-auto">
        
        {/* Map Area */}
        <div className="w-full lg:w-2/3 flex flex-col bg-gray-50 dark:bg-gray-900 relative h-full flex-grow z-0 transition-colors">
          <div className="p-2 sm:p-3 bg-white dark:bg-gray-800 z-10 shadow-sm flex justify-center items-center relative transition-colors">
            
            {/* Show heard text for debugging */}
            {heardText && (
              <div className="absolute left-4 top-1/2 -translate-y-1/2 bg-gray-800 text-white text-xs px-3 py-1.5 rounded-full shadow-lg z-20">
                {heardText}
              </div>
            )}

          </div>
          
          <div className="flex-grow overflow-hidden relative">
            <HospitalMap locations={locations} route={route} />
          </div>
        </div>

        {/* Navigation Controls (Bottom Sheet on Mobile, Side Panel on Desktop) */}
        <div className="lg:w-1/3 bg-white dark:bg-gray-800 p-5 rounded-t-3xl lg:rounded-none shadow-[0_-10px_30px_rgba(0,0,0,0.08)] dark:shadow-[0_-10px_30px_rgba(0,0,0,0.3)] lg:shadow-[-5px_0_20px_rgba(0,0,0,0.05)] border-t lg:border-t-0 lg:border-l border-gray-100 dark:border-gray-700 flex flex-col absolute lg:relative bottom-0 left-0 w-full max-h-[45dvh] lg:max-h-full h-auto lg:h-full z-30 overflow-y-auto pb-8 lg:pb-5 transition-colors">
          
          {/* Drag Handle for Mobile */}
          <div className="w-12 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full mx-auto mb-4 lg:hidden shrink-0"></div>

          <div className="flex justify-between items-center mb-5 hidden lg:flex shrink-0">
             <h2 className="text-xl font-bold text-gray-800 dark:text-white transition-colors">
              {language === 'hi' ? 'मार्ग खोजें' : 'Find Your Way'}
            </h2>
            <div className="flex gap-2">
               <button onClick={handleEmergency} className="bg-red-50 hover:bg-red-100 dark:bg-red-900/30 dark:hover:bg-red-900/50 p-2.5 rounded-lg text-red-600 dark:text-red-400 transition" title="Emergency">
                <AlertTriangle size={20} />
               </button>
               <button onClick={toggleQRScanner} className="bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 p-2.5 rounded-lg text-gray-600 dark:text-gray-300 transition" title="Scan QR">
                <QrCode size={20} />
               </button>
               <button onClick={startListening} className={`p-2.5 rounded-lg text-white transition shadow-md ${isListening ? 'bg-red-500 animate-pulse' : 'bg-orange-500 hover:bg-orange-600 dark:bg-orange-400 dark:hover:bg-orange-500'}`} title="Voice Command">
                <Mic size={20} />
               </button>
            </div>
          </div>
          
          <div className="space-y-4 shrink-0">
            {/* Mobile Action Buttons (Visible only on mobile) */}
            <div className="lg:hidden flex gap-2 mb-2">
              <button onClick={handleEmergency} className="flex-1 bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400 border border-red-100 dark:border-red-900/50 rounded-xl p-3 flex items-center justify-center gap-2 font-bold text-sm active:scale-95 transition-all shadow-sm">
                <AlertTriangle size={18} />
                {language === 'hi' ? 'इमरजेंसी' : 'Emergency'}
              </button>
              <button onClick={toggleQRScanner} className="w-12 shrink-0 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-xl flex items-center justify-center active:scale-95 transition-all shadow-sm">
                <QrCode size={20} />
              </button>
              <button onClick={startListening} className={`w-12 shrink-0 rounded-xl flex items-center justify-center active:scale-95 transition-all shadow-sm text-white ${isListening ? 'bg-red-500 animate-pulse' : 'bg-orange-500'}`}>
                <Mic size={20} />
              </button>
            </div>

            <div className={`transition-all duration-500 rounded-xl ${highlightStart ? 'ring-4 ring-green-500 ring-offset-2 dark:ring-offset-gray-800 animate-pulse' : ''}`}>
                <SearchableDropdown 
                  label={language === 'hi' ? 'वर्तमान स्थान' : 'Current Location'}
                  value={start}
                  onChange={(val) => {
                    setStart(val);
                    if (highlightStart) {
                      setHighlightStart(false);
                      // Auto trigger navigation if destination is already set
                      if (destination) {
                         setTimeout(() => setVoiceTriggerNavigate(true), 100);
                      }
                    }
                  }}
                  locations={locations}
                  language={language}
                />
              </div>

            <div>
                <SearchableDropdown 
                  label={language === 'hi' ? 'मंजिल' : 'Destination'}
                  value={destination}
                  onChange={setDestination}
                  locations={locations}
                  language={language}
                />
              </div>

            <div className="flex gap-4 pt-1 pb-1">
              <label className="flex items-center gap-3 cursor-pointer group bg-gray-50 dark:bg-gray-800 p-3 rounded-xl border border-gray-100 dark:border-gray-700 transition-colors flex-1">
                <input 
                  type="checkbox" 
                  checked={isAccessible}
                  onChange={(e) => setIsAccessible(e.target.checked)}
                  className="w-5 h-5 text-orange-500 rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 focus:ring-orange-400"
                />
                <span className="text-sm font-bold text-gray-700 dark:text-gray-300 group-hover:text-orange-600 dark:group-hover:text-orange-300 transition-colors">
                  {language === 'hi' ? 'व्हीलचेयर' : 'Wheelchair'}
                </span>
              </label>
              <label className="flex items-center gap-3 cursor-pointer group bg-gray-50 dark:bg-gray-800 p-3 rounded-xl border border-gray-100 dark:border-gray-700 transition-colors flex-1">
                <input 
                  type="checkbox" 
                  checked={autoAudio}
                  onChange={(e) => setAutoAudio(e.target.checked)}
                  className="w-5 h-5 text-orange-500 rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 focus:ring-orange-400"
                />
                <span className="text-sm font-bold text-gray-700 dark:text-gray-300 group-hover:text-orange-600 dark:group-hover:text-orange-300 transition-colors">
                  {language === 'hi' ? 'ऑटो ऑडियो' : 'Auto Audio'}
                </span>
              </label>
            </div>

            <div className="flex gap-2 w-full mt-1">
              <button 
                id="navigate-btn"
                onClick={() => handleNavigate()}
                disabled={loading || !start || !destination || start === destination}
                className="flex-1 bg-orange-500 hover:bg-orange-600 dark:bg-orange-400 dark:hover:bg-orange-500 text-white font-black py-3.5 rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-[0_4px_14px_0_rgba(249,115,22,0.39)] text-base tracking-wide active:scale-95"
              >
                {loading ? (language === 'hi' ? 'खोज रहा है...' : 'Calculating...') : (language === 'hi' ? 'दिशा-निर्देश' : 'Get Directions')}
              </button>
              
              <button
                onClick={handleShare}
                disabled={!start}
                className="w-14 shrink-0 bg-green-100 hover:bg-green-200 dark:bg-green-900/40 dark:hover:bg-green-900/60 text-green-700 dark:text-green-400 font-black rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-sm flex items-center justify-center active:scale-95"
                title={language === 'hi' ? 'लोकेशन शेयर करें' : 'Share Location'}
              >
                <Share2 size={22} />
              </button>
            </div>

            {error && (
              <div className="p-3 bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-400 rounded-xl text-sm font-semibold border border-red-100 dark:border-red-900/50 mt-2 flex items-start gap-2 transition-colors">
                <svg className="w-5 h-5 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
                </svg>
                {error}
              </div>
            )}
          </div>

          {/* Route Instructions */}
          {route && route.path_found && (
            <div className="mt-5 pt-5 border-t border-gray-100 dark:border-gray-700 transition-colors">
              
              {/* Estimated Walking Time Banner */}
              <div className="bg-orange-50 dark:bg-orange-900/30 border border-orange-100 dark:border-orange-900/50 rounded-xl p-3 mb-4 flex items-center gap-3">
                <div className="bg-orange-100 dark:bg-orange-800 text-orange-500 dark:text-orange-200 w-10 h-10 rounded-full flex items-center justify-center shrink-0 font-black shadow-sm">
                  {Math.ceil(route.total_distance * 0.063 / 84) < 1 ? '<1' : Math.ceil(route.total_distance * 0.063 / 84)}
                </div>
                <div>
                  <p className="text-sm font-black text-gray-800 dark:text-gray-100">
                    {language === 'hi' ? 'अनुमानित समय' : 'Estimated Walk Time'}
                  </p>
                  <p className="text-xs font-semibold text-gray-500 dark:text-gray-400">
                    {language === 'hi' ? 'लगभग' : 'approx.'} {Math.ceil(route.total_distance * 0.063 / 84) < 1 ? '1' : Math.ceil(route.total_distance * 0.063 / 84)} {language === 'hi' ? 'मिनट' : 'minute'}
                  </p>
                </div>
              </div>

              <div className="flex justify-between items-center mb-4">
                <h3 className="text-base font-black text-gray-800 dark:text-white transition-colors">
                  {language === 'hi' ? 'कदम-दर-कदम' : 'Step-by-Step'}
                </h3>
                <button 
                  onClick={speakRoute}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold transition-all shadow-sm active:scale-95 ${isSpeaking ? 'bg-red-100 text-red-700 hover:bg-red-200' : 'bg-green-100 text-green-800 hover:bg-green-200'}`}
                >
                  {isSpeaking ? '🛑 Stop' : '🔊 Speak'}
                </button>
              </div>
              
              <div className="space-y-3">
                {route.steps.map((step, idx) => (
                  <div key={idx} className="flex gap-3 items-start">
                    <div className="flex flex-col items-center">
                      <div className={`w-7 h-7 rounded-full flex items-center justify-center font-black text-xs shadow-sm transition-colors ${idx === 0 ? 'bg-green-100 dark:bg-green-900/50 text-green-700 dark:text-green-400 border border-green-200 dark:border-green-800' : idx === route.steps.length - 1 ? 'bg-red-100 dark:bg-red-900/50 text-red-700 dark:text-red-400 border border-red-200 dark:border-red-800' : 'bg-orange-50 dark:bg-orange-900/30 text-orange-600 dark:text-orange-300 border border-orange-200 dark:border-orange-800'}`}>
                        {idx + 1}
                      </div>
                      {idx < route.steps.length - 1 && (
                        <div className="w-0.5 h-full bg-gray-200 dark:bg-gray-700 my-1 min-h-[2rem] transition-colors"></div>
                      )}
                    </div>
                    <div className="pt-0.5 pb-2">
                      <p className="font-bold text-gray-800 dark:text-gray-200 text-sm leading-tight transition-colors">
                        {language === 'hi' ? step.instruction_hi : step.instruction_en}
                      </p>

                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          
        </div>
      </div>

      {/* Usage Stats Modal */}
      {showStats && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className={`w-full max-w-sm rounded-3xl p-6 shadow-2xl transition-colors ${isDarkMode ? 'bg-gray-800 text-white' : 'bg-white text-gray-800'}`}>
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-bold flex items-center gap-2">
                <BarChart2 className={isDarkMode ? "text-orange-300" : "text-orange-500"} />
                {language === 'hi' ? 'उपयोग आंकड़े' : 'Usage Statistics'}
              </h2>
              <button onClick={() => setShowStats(false)} className={`p-2 rounded-full ${isDarkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-100'}`}>
                <X size={20} />
              </button>
            </div>
            {!statsData ? (
              <div className="flex justify-center p-8">
                <div className="w-8 h-8 border-4 border-orange-400 border-t-transparent rounded-full animate-spin"></div>
              </div>
            ) : (
              <div className="space-y-4">
                <div className={`p-4 rounded-2xl ${isDarkMode ? 'bg-gray-700' : 'bg-orange-50'}`}>
                  <p className="text-sm font-medium opacity-70 mb-1">{language === 'hi' ? 'कुल उपयोगकर्ता' : 'Total Unique Users'}</p>
                  <p className="text-4xl font-black text-orange-400">{statsData.total_unique_users}</p>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className={`p-4 rounded-2xl ${isDarkMode ? 'bg-gray-700' : 'bg-gray-50'}`}>
                    <p className="text-xs font-medium opacity-70 mb-1">{language === 'hi' ? 'इस महीने' : 'This Month'}</p>
                    <p className="text-2xl font-bold">{statsData.users_this_month}</p>
                  </div>
                  <div className={`p-4 rounded-2xl ${isDarkMode ? 'bg-gray-700' : 'bg-gray-50'}`}>
                    <p className="text-xs font-medium opacity-70 mb-1">{language === 'hi' ? 'औसत / महीना' : 'Avg / Month'}</p>
                    <p className="text-2xl font-bold">{statsData.average_users_per_month}</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* QR Scanner Full Screen Overlay */}
      {showQRScanner && (
        <div className="fixed inset-0 bg-black z-50 flex flex-col">
          <div className="flex justify-between items-center p-4 text-white z-10 bg-gradient-to-b from-black/80 to-transparent">
            <h2 className="text-lg font-bold">
              {language === 'hi' ? 'QR कोड स्कैन करें' : 'Scan QR Code'}
            </h2>
            <button 
              onClick={() => { setShowQRScanner(false); setQrScanStatus(''); }}
              className="p-2 bg-white/10 rounded-full hover:bg-white/20 transition-colors"
            >
              <X size={24} />
            </button>
          </div>
          <div className="flex-grow relative overflow-hidden flex items-center justify-center">
            <Scanner 
              onScan={(result) => handleQRScan(result)} 
              onError={(error) => {
                console.error("Scanner error:", error);
                setQrScanStatus(`Camera error: ${error?.message || error}`);
              }}
              constraints={{ facingMode: 'environment' }}
              formats={['qr_code']}
              styles={{ container: { width: '100%', height: '100%' } }}
            />
            {/* Target reticle overlay */}
            <div className="absolute inset-0 pointer-events-none border-[40px] border-black/40">
              <div className="w-full h-full border-2 border-white/50 rounded-lg relative">
                <div className="absolute top-0 left-0 w-8 h-8 border-t-4 border-l-4 border-orange-400 rounded-tl-lg -ml-0.5 -mt-0.5"></div>
                <div className="absolute top-0 right-0 w-8 h-8 border-t-4 border-r-4 border-orange-400 rounded-tr-lg -mr-0.5 -mt-0.5"></div>
                <div className="absolute bottom-0 left-0 w-8 h-8 border-b-4 border-l-4 border-orange-400 rounded-bl-lg -ml-0.5 -mb-0.5"></div>
                <div className="absolute bottom-0 right-0 w-8 h-8 border-b-4 border-r-4 border-orange-400 rounded-br-lg -mr-0.5 -mb-0.5"></div>
              </div>
            </div>
          </div>
          <div className="p-6 text-center text-white bg-black/90">
            {qrScanStatus ? (
              <p className="text-sm text-yellow-300 font-semibold">{qrScanStatus}</p>
            ) : (
              <p className="text-sm opacity-80">
                {language === 'hi' 
                  ? 'अस्पताल में लगे किसी भी Disha QR कोड को कैमरे के सामने लाएँ।' 
                  : 'Point the camera at any Disha QR code in the hospital.'}
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default App

