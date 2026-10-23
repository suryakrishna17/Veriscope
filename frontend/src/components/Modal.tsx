import { useEffect, useRef, type ReactNode } from "react";

interface Props {
  open: boolean;
  title: string;
  onClose: () => void;
  children: ReactNode;
  footer?: ReactNode;
}

/** Native <dialog>: focus trapping, Escape to close and inert background come for free. */
export function Modal({ open, title, onClose, children, footer }: Props) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const d = ref.current;
    if (!d) return;
    if (open && !d.open) d.showModal();
    if (!open && d.open) d.close();
  }, [open]);
  return (
    <dialog ref={ref} className="modal" onClose={onClose} aria-labelledby="modal-title">
      <header className="modal-head">
        <h2 id="modal-title">{title}</h2>
        <button className="icon-btn" onClick={onClose} aria-label="Close">×</button>
      </header>
      <div className="modal-body">{children}</div>
      {footer && <footer className="modal-foot">{footer}</footer>}
    </dialog>
  );
}
