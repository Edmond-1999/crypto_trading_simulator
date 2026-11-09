import { CheckCircle2, X } from "lucide-react";

type Props = {
  message: string;
  onDismiss: () => void;
};

export default function NoticeBanner({ message, onDismiss }: Props) {
  return (
    <div className="success-banner" role="status">
      <CheckCircle2 size={17} />
      <span>{message}</span>
      <button
        className="banner-close"
        aria-label="Dismiss message"
        onClick={onDismiss}
      >
        <X size={15} />
      </button>
    </div>
  );
}
