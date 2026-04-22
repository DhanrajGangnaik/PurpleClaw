import { useTheme } from '../hooks/useTheme';
import type { ThemeMode } from '../context/ThemeContext';

const options: { value: ThemeMode; label: string }[] = [
  { value: 'dark', label: 'Dark' },
  { value: 'light', label: 'Light' },
];

export function ThemeSwitcher() {
  const { theme, setTheme } = useTheme();

  return (
    <div className="theme-segmented" role="group" aria-label="Theme mode">
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          onClick={() => setTheme(option.value)}
          className={`theme-segment ${theme === option.value ? 'theme-segment-active' : ''}`}
          aria-pressed={theme === option.value}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
