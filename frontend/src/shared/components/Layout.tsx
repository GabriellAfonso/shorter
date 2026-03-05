import { Outlet } from "react-router-dom";
import { Navbar } from "./Navbar";
import { Toaster } from "./Toaster";

export function Layout() {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="container py-8">
        <Outlet />
      </main>
      <Toaster />
    </div>
  );
}
