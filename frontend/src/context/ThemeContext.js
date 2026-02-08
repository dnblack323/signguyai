import { createContext, useContext } from 'react';

const ThemeContext = createContext();

export function ThemeProvider({ children }) {
  // Fixed unified blended theme - no toggle functionality
  // The app uses a dark shell with light content panels
  
  return (
    <ThemeContext.Provider value={{ theme: 'blended' }}>
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
