import { Bell, LogOut, User } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

interface HeaderProps { title?: string; }

export function Header({ title }: HeaderProps) {
  const { user, logout } = useAuth();
  return (
    <header className="h-14 border-b border-gray-800/80 bg-gray-950/90 backdrop-blur flex items-center px-6 gap-4">
      {title && <h1 className="text-sm font-semibold text-gray-300">{title}</h1>}
      <div className="ml-auto flex items-center gap-3">
        <button className="p-1.5 rounded-lg text-gray-500 hover:text-gray-300 hover:bg-gray-800 transition-colors">
          <Bell className="w-4 h-4" />
        </button>
        <div className="flex items-center gap-2 text-sm">
          <div className="w-7 h-7 rounded-full bg-purple-800 flex items-center justify-center">
            <User className="w-3.5 h-3.5 text-purple-300" />
          </div>
          <span className="text-gray-400 hidden sm:block">{user?.username}</span>
          <span className="badge badge-purple text-xs hidden sm:block">{user?.role}</span>
        </div>
        <button onClick={logout} className="p-1.5 rounded-lg text-gray-500 hover:text-red-400 hover:bg-gray-800 transition-colors" title="Sign out">
          <LogOut className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
}
