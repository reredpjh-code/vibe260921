import Link from "next/link";

export function SiteHeader() {
  return (
    <header className="border-b bg-background">
      <div className="mx-auto flex h-14 max-w-4xl items-center justify-between px-4">
        <Link href="/board" className="text-lg font-semibold tracking-tight">
          DemoBoard
        </Link>
        <nav className="text-sm text-muted-foreground">
          <Link href="/board/new" className="hover:text-foreground">
            글쓰기
          </Link>
        </nav>
      </div>
    </header>
  );
}
