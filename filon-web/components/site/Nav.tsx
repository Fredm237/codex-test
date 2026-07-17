import { primaryNav, site } from "@/lib/site";
import { Logo } from "./Logo";
import { ThemeToggle } from "./ThemeToggle";
import { Button } from "@/components/ui/Button";

export function Nav() {
  return (
    <header style={{ position: "sticky", top: 0, zIndex: 50 }}>
      <nav
        style={{
          margin: "14px auto 0",
          maxWidth: 1200,
          width: "calc(100% - 32px)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 20,
          padding: "11px 12px 11px 20px",
          borderRadius: "var(--r-full)",
          background: "color-mix(in srgb, var(--bg-2) 62%, transparent)",
          border: "1px solid var(--border)",
          backdropFilter: "blur(20px) saturate(1.4)",
          WebkitBackdropFilter: "blur(20px) saturate(1.4)",
          boxShadow: "var(--shadow-soft)",
        }}
      >
        <a href="/" style={{ display: "flex", alignItems: "center", gap: 11, fontWeight: 600, fontSize: 19, letterSpacing: "-0.04em" }}>
          <Logo />
          {site.name}
        </a>
        <div className="filon-navlinks" style={{ display: "flex", alignItems: "center", gap: 4 }}>
          {primaryNav.map((item) => (
            <a
              key={item.href}
              href={item.href}
              style={{ padding: "8px 13px", borderRadius: "var(--r-full)", color: "var(--text-dim)", fontSize: 14.5, fontWeight: 500 }}
            >
              {item.label}
            </a>
          ))}
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <ThemeToggle />
          <Button href="/#installer" style={{ padding: "11px 20px", fontSize: 14.5 }}>
            Installer FILON
          </Button>
        </div>
      </nav>
    </header>
  );
}
