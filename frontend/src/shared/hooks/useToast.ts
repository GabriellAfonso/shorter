/**
 * Minimal toast hook — compatible with shadcn/ui's toast pattern.
 * Stores toasts in module-level state and dispatches updates.
 */
import * as React from "react";

const TOAST_LIMIT = 5;
const TOAST_REMOVE_DELAY = 5000;

type ToastVariant = "default" | "destructive";

export interface ToastMessage {
  id: string;
  title?: string;
  description?: string;
  variant?: ToastVariant;
  open: boolean;
}

type Action =
  | { type: "ADD_TOAST"; toast: ToastMessage }
  | { type: "UPDATE_TOAST"; id: string; toast: Partial<ToastMessage> }
  | { type: "DISMISS_TOAST"; id: string }
  | { type: "REMOVE_TOAST"; id: string };

let count = 0;
function genId() {
  count = (count + 1) % Number.MAX_SAFE_INTEGER;
  return String(count);
}

const listeners: Array<(state: ToastMessage[]) => void> = [];
let memoryState: ToastMessage[] = [];

function dispatch(action: Action) {
  memoryState = reducer(memoryState, action);
  listeners.forEach((l) => l(memoryState));
}

function reducer(state: ToastMessage[], action: Action): ToastMessage[] {
  switch (action.type) {
    case "ADD_TOAST":
      return [action.toast, ...state].slice(0, TOAST_LIMIT);
    case "UPDATE_TOAST":
      return state.map((t) => (t.id === action.id ? { ...t, ...action.toast } : t));
    case "DISMISS_TOAST":
      return state.map((t) => (t.id === action.id ? { ...t, open: false } : t));
    case "REMOVE_TOAST":
      return state.filter((t) => t.id !== action.id);
    default:
      return state;
  }
}

export function toast({
  title,
  description,
  variant = "default",
}: Pick<ToastMessage, "title" | "description" | "variant">) {
  const id = genId();
  dispatch({ type: "ADD_TOAST", toast: { id, title, description, variant, open: true } });
  setTimeout(() => dispatch({ type: "DISMISS_TOAST", id }), TOAST_REMOVE_DELAY);
  setTimeout(() => dispatch({ type: "REMOVE_TOAST", id }), TOAST_REMOVE_DELAY + 300);
  return id;
}

export function useToast() {
  const [toasts, setToasts] = React.useState<ToastMessage[]>(memoryState);

  React.useEffect(() => {
    listeners.push(setToasts);
    return () => {
      const i = listeners.indexOf(setToasts);
      if (i > -1) listeners.splice(i, 1);
    };
  }, []);

  return { toasts, toast };
}
