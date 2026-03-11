/**
 * Root provider tree.
 * Hydrates accounts state from localStorage on app startup.
 */
import { useEffect } from "react";
import { RouterProvider } from "react-router-dom";
import { router } from "./router";
import { useAuthStore } from "@/features/auth/store/authStore";

export function Providers() {
  const { hydrateFromStorage } = useAuthStore();

  useEffect(() => {
    hydrateFromStorage();
  }, [hydrateFromStorage]);

  return <RouterProvider router={router} />;
}
