import { useTheme } from '../hooks/useTheme';

interface LogoProps {
  variant?: 'dark' | 'light';
  className?: string;
}

const logoPaths = {
  dark: '/logo/PURPLECLAW-DARK.svg',
  light: '/logo/PURPLECLAW-LIGHT.svg',
};

export function Logo({ variant, className = 'h-8 w-auto' }: LogoProps) {
  const { theme } = useTheme();
  const activeVariant = variant ?? theme;

  return <img src={logoPaths[activeVariant]} alt="PurpleClaw Security Platform" className={className} />;
}
