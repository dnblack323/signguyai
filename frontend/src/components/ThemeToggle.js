import { useTheme } from '../context/ThemeContext';
import { Button } from './ui/button';
import { Moon, Sun } from 'lucide-react';

export default function ThemeToggle({ collapsed = false }) {
  const { theme, toggleTheme } = useTheme();

  return (
    <Button
      variant="ghost"
      size={collapsed ? "icon" : "default"}
      onClick={toggleTheme}
      className="w-full justify-start gap-3 text-muted-foreground hover:text-foreground hover:bg-muted/50"
      data-testid="theme-toggle"
    >
      {theme === 'dark' ? (
        <>
          <Sun className="h-5 w-5" />
          {!collapsed && <span>Light Mode</span>}
        </>
      ) : (
        <>
          <Moon className="h-5 w-5" />
          {!collapsed && <span>Dark Mode</span>}
        </>
      )}
    </Button>
  );
}
