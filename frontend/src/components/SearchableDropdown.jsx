import React, { useState, useRef, useEffect } from 'react';

const SearchableDropdown = ({ label, value, onChange, locations, language }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const wrapperRef = useRef(null);
  const desktopInputRef = useRef(null);
  const mobileInputRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(event) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [wrapperRef]);

  // Focus the correct input when opened
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => {
        if (window.innerWidth >= 1024) {
          if (desktopInputRef.current) desktopInputRef.current.focus();
        } else {
          if (mobileInputRef.current) mobileInputRef.current.focus();
        }
      }, 100);
    }
  }, [isOpen]);

  const selectedLocation = locations.find(loc => loc.id === value);
  const displayText = selectedLocation 
    ? (language === 'hi' ? (selectedLocation.name_hi || selectedLocation.name) : selectedLocation.name)
    : '';

  const filteredLocations = locations.filter(loc => {
    // Only show valid room locations, ignore corridor waypoints
    if (loc.is_room === false || loc.is_room === 0) return false;
    
    const searchLower = searchTerm.toLowerCase();
    const nameEn = loc.name ? loc.name.toLowerCase() : '';
    const nameHi = loc.name_hi ? loc.name_hi.toLowerCase() : '';
    return nameEn.includes(searchLower) || nameHi.includes(searchLower);
  });

  const renderList = () => {
    if (filteredLocations.length > 0) {
      return filteredLocations.map((loc) => (
        <div
          key={loc.id}
          className={`p-3 lg:p-2 text-base lg:text-sm cursor-pointer hover:bg-blue-50 dark:hover:bg-blue-900/30 transition-colors border-b lg:border-none border-gray-100 dark:border-gray-800 ${value === loc.id ? 'bg-blue-50 dark:bg-blue-900/30 font-bold text-blue-700 dark:text-blue-300' : 'text-gray-700 dark:text-gray-300'}`}
          onClick={() => {
            onChange(loc.id);
            setIsOpen(false);
          }}
        >
          {language === 'hi' ? (loc.name_hi || loc.name) : loc.name}
        </div>
      ));
    } else {
      return (
        <div className="p-4 text-sm text-gray-500 text-center">
          {language === 'hi' ? 'कोई परिणाम नहीं' : 'No matches found'}
        </div>
      );
    }
  };

  return (
    <div className="relative w-full" ref={wrapperRef}>
      <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">{label}</label>
      <div 
        className="w-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-3 flex justify-between items-center cursor-pointer shadow-sm hover:border-blue-400 transition-colors"
        onClick={() => { setIsOpen(!isOpen); setSearchTerm(''); }}
      >
        <span className={`text-sm font-semibold ${displayText ? 'text-gray-800 dark:text-gray-200' : 'text-gray-400'}`}>
          {displayText || (language === 'hi' ? 'स्थान चुनें...' : 'Select location...')}
        </span>
        <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path></svg>
      </div>

      {isOpen && (
        <>
          {/* Mobile Full-Screen Modal (Visible only on small screens) */}
          <div className="fixed inset-0 bg-white dark:bg-gray-900 z-[100] flex flex-col lg:hidden animate-in slide-in-from-bottom-4 duration-200">
            {/* Header / Search Bar */}
            <div className="flex items-center gap-3 p-4 border-b border-gray-200 dark:border-gray-800 shadow-sm bg-white dark:bg-gray-900">
              <button onClick={() => setIsOpen(false)} className="p-2 -ml-2 text-gray-600 dark:text-gray-300 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path>
                </svg>
              </button>
              <input
                ref={mobileInputRef}
                type="text"
                className="flex-1 bg-transparent text-lg border-none focus:ring-0 text-gray-900 dark:text-white placeholder-gray-400 p-0"
                placeholder={language === 'hi' ? 'खोजें...' : 'Search...'}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            {/* List Results */}
            <div className="flex-1 overflow-y-auto bg-gray-50 dark:bg-gray-900/50">
              {renderList()}
            </div>
          </div>

          {/* Desktop Inline Dropdown (Visible only on large screens) */}
          <div className="hidden lg:flex absolute z-50 w-full mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-lg max-h-60 flex-col overflow-hidden">
            <div className="p-2 border-b border-gray-100 dark:border-gray-700">
              <input
                ref={desktopInputRef}
                type="text"
                className="w-full bg-gray-50 dark:bg-gray-700 border-none rounded-lg p-2 text-sm focus:ring-2 focus:ring-blue-500 dark:text-white"
                placeholder={language === 'hi' ? 'खोजें...' : 'Search...'}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                onClick={(e) => e.stopPropagation()}
              />
            </div>
            <div className="overflow-y-auto">
              {renderList()}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default SearchableDropdown;
