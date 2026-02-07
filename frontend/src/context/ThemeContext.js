import { createContext, useContext, useState, useEffect } from 'react';

const ThemeContext = createContext();

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(() => {
    // Check localStorage first
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme && ['dark', 'light', 'contrast'].includes(savedTheme)) {
      return savedTheme;
    }
    // Default to dark
    return 'dark';
  });

  useEffect(() => {
    const root = window.document.documentElement;
    
    // Remove all theme classes first
    root.classList.remove('light', 'dark', 'contrast');
    
    // Add the current theme class (dark is default in :root, others need class)
    if (theme === 'light') {
      root.classList.add('light');
    } else if (theme === 'contrast') {
      root.classList.add('contrast');
    }
    
    // Save to localStorage
    localStorage.setItem('theme', theme);
  }, [theme]);

  // Cycle through themes: dark -> light -> contrast -> dark
  const cycleTheme = () => {
    setTheme(prev => {
      if (prev === 'dark') return 'light';
      if (prev === 'light') return 'contrast';
      return 'dark';
    });
  };

  // Legacy toggle for backwards compatibility
  const toggleTheme = cycleTheme;

  return (
    <ThemeContext.Provider value={{ theme, setTheme, toggleTheme, cycleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
