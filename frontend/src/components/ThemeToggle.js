import { useTheme } from '../context/ThemeContext';
import { Button } from './ui/button';
import { Moon, Sun, Monitor } from 'lucide-react';

export default function ThemeToggle({ collapsed = false }) {
  const { theme, cycleTheme } = useTheme();

  const getIcon = () => {
    if (theme === 'dark') return <Sun className="h-5 w-5" />;
    if (theme === 'light') return <Monitor className="h-5 w-5" />;
    return <Moon className="h-5 w-5" />;
  };

  const getLabel = () => {
    if (theme === 'dark') return 'Light Mode';
    if (theme === 'light') return 'Contrast Mode';
    return 'Dark Mode';
  };

  const getDescription = () => {
    if (theme === 'dark') return 'Switch to light theme';
    if (theme === 'light') return 'Switch to contrast (dark bg, light cards)';
    return 'Switch to dark theme';
  };

  return (
    <Button
      variant="ghost"
      size={collapsed ? "icon" : "default"}
      onClick={cycleTheme}
      className="w-full justify-start gap-3 text-muted-foreground hover:text-foreground hover:bg-muted/50"
      data-testid="theme-toggle"
      title={getDescription()}
    >
      {getIcon()}
      {!collapsed && <span>{getLabel()}</span>}
    </Button>
  );
}
