import { Plus, Wallet as WalletIcon } from "lucide-react";

type Props = {
  onCreateWallet: () => void;
};

export default function NoWalletPanel({ onCreateWallet }: Props) {
  return (
    <section className="panel no-wallet-panel">
      <span className="empty-icon">
        <WalletIcon size={25} />
      </span>
      <h2>Set up your first wallet</h2>
      <p>
        Create a demo wallet to view balances and start simulated spot trading.
      </p>
      <button className="primary-button" onClick={onCreateWallet}>
        <Plus size={17} /> Create wallet
      </button>
    </section>
  );
}
