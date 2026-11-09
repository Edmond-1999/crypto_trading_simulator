import { ChevronDown, Plus, Wallet as WalletIcon } from "lucide-react";
import type { NavigationSection, User, Wallet } from "../types";

type Props = {
  activeSection: NavigationSection;
  wallets: Wallet[];
  walletId: string;
  walletsLoading: boolean;
  user: User | null;
  fallbackEmail: string;
  onSelectWallet: (value: string) => void;
  onCreateWallet: () => void;
};

export default function AppTopbar({
  activeSection,
  wallets,
  walletId,
  walletsLoading,
  user,
  fallbackEmail,
  onSelectWallet,
  onCreateWallet,
}: Props) {
  return (
    <header className="topbar sticky top-0 z-[8] flex min-h-[88px] items-center justify-between gap-5 px-[38px] py-[17px] max-[1250px]:px-[25px] max-[620px]:static max-[620px]:flex-col max-[620px]:items-start max-[620px]:gap-[14px] max-[620px]:px-[17px] max-[620px]:py-[19px]">
      <div className="topbar-heading">
        <span className="eyebrow">YOUR WORKSPACE</span>
        <h1>{activeSection}</h1>
      </div>

      <div className="topbar-actions flex items-center gap-[14px] max-[620px]:w-full max-[620px]:gap-[9px] max-[380px]:gap-[6px]">
        <span className="live-indicator">
          <span className="online-dot" />
          Market feed
        </span>

        <div className="wallet-selector flex min-w-[150px] items-center gap-[9px] rounded-[10px] border border-[var(--border)] bg-[var(--panel)] px-[11px] py-[10px] max-[620px]:min-w-0 max-[620px]:flex-1 max-[380px]:gap-[5px] max-[380px]:px-[7px] max-[380px]:py-[9px]">
          <WalletIcon size={17} />
          <select
            aria-label="Select wallet"
            value={walletId}
            onChange={(event) => onSelectWallet(event.target.value)}
            disabled={walletsLoading || wallets.length === 0}
          >
            {wallets.length === 0 && <option value="">No wallets</option>}
            {wallets.map((wallet) => (
              <option key={wallet.id} value={String(wallet.id)}>
                {wallet.name}
              </option>
            ))}
          </select>
          <ChevronDown size={14} />
        </div>

        <button
          className="icon-button"
          title="Create wallet"
          aria-label="Create wallet"
          onClick={onCreateWallet}
        >
          <Plus size={18} />
        </button>

        <div className="user-avatar max-[380px]:h-8 max-[380px]:w-8">
          {(user?.email || fallbackEmail || "U").slice(0, 1).toUpperCase()}
        </div>
      </div>
    </header>
  );
}
