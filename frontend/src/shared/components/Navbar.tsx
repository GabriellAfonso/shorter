import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Link2, LayoutDashboard, TableProperties, LogOut, Menu, X } from "lucide-react";
import { Button } from "@/shared/components/ui/button";
import { Separator } from "@/shared/components/ui/separator";
import { useAuthStore } from "@/features/auth/store/authStore";
import { cn } from "@/shared/lib/utils";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/links", label: "All Links", icon: TableProperties },
];

export function Navbar() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center justify-between">
        {/* Logo */}
        <Link to="/dashboard" className="flex items-center gap-2 font-bold text-lg shrink-0">
          <Link2 className="h-5 w-5 text-primary" />
          <span>Shorter</span>
        </Link>

        {/* Desktop nav */}
        {user && (
          <nav className="hidden sm:flex items-center gap-1">
            {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
              <Button
                key={to}
                variant="ghost"
                size="sm"
                asChild
                className={cn(pathname === to && "bg-accent text-accent-foreground")}
              >
                <Link to={to}>
                  <Icon className="mr-1.5 h-4 w-4" />
                  {label}
                </Link>
              </Button>
            ))}

            <Separator orientation="vertical" className="h-5 mx-1" />

            <div className="flex items-center gap-2 pl-1">
              <span className="text-sm text-muted-foreground hidden md:block truncate max-w-[140px]">
                {user.email}
              </span>
              <Button variant="ghost" size="sm" onClick={handleLogout}>
                <LogOut className="mr-1 h-4 w-4" />
                Logout
              </Button>
            </div>
          </nav>
        )}

        {/* Mobile hamburger */}
        {user && (
          <Button
            variant="ghost"
            size="icon"
            className="sm:hidden"
            onClick={() => setMobileOpen((v) => !v)}
            aria-label="Toggle navigation menu"
          >
            {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </Button>
        )}
      </div>

      {/* Mobile dropdown */}
      {user && mobileOpen && (
        <div className="sm:hidden border-t px-4 py-3 space-y-1 bg-background">
          {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
            <Button
              key={to}
              variant="ghost"
              size="sm"
              className={cn("w-full justify-start", pathname === to && "bg-accent")}
              asChild
              onClick={() => setMobileOpen(false)}
            >
              <Link to={to}>
                <Icon className="mr-2 h-4 w-4" />
                {label}
              </Link>
            </Button>
          ))}
          <Separator className="my-2" />
          <Button
            variant="ghost"
            size="sm"
            className="w-full justify-start text-destructive hover:text-destructive"
            onClick={handleLogout}
          >
            <LogOut className="mr-2 h-4 w-4" />
            Logout
          </Button>
        </div>
      )}
    </header>
  );
}
