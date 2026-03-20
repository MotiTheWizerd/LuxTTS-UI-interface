import { HiMicrophone, HiCog, HiHome, HiClock, HiFolder } from 'react-icons/hi';
import NavItem from './NavItem';

export default function Sidebar() {
  return (
    <aside className="w-56 bg-gray-900 border-r border-gray-800 flex flex-col">
      <div className="p-4 border-b border-gray-800">
        <h1 className="text-lg font-bold flex items-center gap-2">
          <HiMicrophone className="text-indigo-400" />
          LuxTTS
        </h1>
      </div>
      <nav className="flex-1 p-3 space-y-1">
        <NavItem icon={<HiHome />} label="Home" to="/" />
        <NavItem icon={<HiMicrophone />} label="Generate" to="/generate" />
        <NavItem icon={<HiFolder />} label="Voices" to="/voices" />
        <NavItem icon={<HiClock />} label="History" to="/history" />
      </nav>
      <div className="p-3 border-t border-gray-800">
        <NavItem icon={<HiCog />} label="Settings" to="/settings" />
      </div>
    </aside>
  );
}
