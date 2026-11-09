import {
  Activity,
  ArrowLeftRight,
  Clock3,
  LayoutDashboard,
  LogOut,
  ShieldCheck,
  Zap,
} from "lucide-react";
import type { NavigationSection } from "../types";

type Props = {
  activeSection: NavigationSection;
  onNavigate: (section: NavigationSection) => void;
  onLogout: () => void;
};

const navigation: {
  section: NavigationSection;
  label: string;
  icon: typeof LayoutDashboard;
}[] = [
  { section: "Dashboard", label: "Dashboard", icon: LayoutDashboard },
  { section: "Markets", label: "Markets", icon: Activity },
  { section: "Trade", label: "Spot trading", icon: ArrowLeftRight },
  { section: "Activity", label: "Order history", icon: Clock3 },
];

export default function AppSidebar({
  activeSection,
  onNavigate,
  onLogout,
}: Props) {
  return (
    <aside className="sidebar fixed inset-y-0 left-0 z-10 flex w-[248px] flex-col border-r border-[var(--border-soft)] bg-[#0d1118] px-[17px] pt-7 pb-[18px] max-[900px]:w-[76px] max-[900px]:items-center max-[900px]:px-[10px] max-[380px]:w-[58px] max-[380px]:px-[7px]">
      <div className="brand">
        <span className="brand-mark">
          <Zap size={22} fill="currentColor" />
        </span>
        <span className="brand-name">
          NEXA<span>TRADE</span>
        </span>
      </div>

      <div className="sidebar-section-label">WORKSPACE</div>
      <nav className="sidebar-nav">
        {navigation.map(({ section, label, icon: Icon }) => (
          <button
            className={`nav-item ${activeSection === section ? "active" : ""}`}
            key={section}
            onClick={() => onNavigate(section)}
          >
            <Icon size={18} />
            <span>{label}</span>
          </button>
        ))}
      </nav>

      <div className="sidebar-spacer min-h-[30px] flex-1" />

      <div className="sidebar-demo-card">
        <span className="demo-icon">
          <ShieldCheck size={18} />
        </span>
        <strong>Demo environment</strong>
        <p>Orders are simulated. No real funds are transferred.</p>
      </div>

      <button className="nav-item logout-button" onClick={onLogout}>
        <LogOut size={18} />
        <span>Sign out</span>
      </button>

      <div className="sidebar-footer">
        <span className="online-dot" />
        Simulator connected
      </div>
    </aside>
  );
}
