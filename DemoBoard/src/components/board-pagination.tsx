import Link from "next/link";
import { Button } from "@/components/ui/button";

function hrefFor(page: number, query?: string) {
  const params = new URLSearchParams();
  if (query) params.set("q", query);
  params.set("page", String(page));
  return `/board?${params.toString()}`;
}

export function BoardPagination({
  page,
  totalPages,
  query,
}: {
  page: number;
  totalPages: number;
  query?: string;
}) {
  if (totalPages <= 1) return null;

  return (
    <div className="flex items-center justify-center gap-3">
      <Button
        variant="outline"
        size="sm"
        nativeButton={false}
        render={<Link href={hrefFor(Math.max(1, page - 1), query)}>이전</Link>}
      />
      <span className="text-sm text-muted-foreground">
        {page} / {totalPages}
      </span>
      <Button
        variant="outline"
        size="sm"
        nativeButton={false}
        render={
          <Link href={hrefFor(Math.min(totalPages, page + 1), query)}>다음</Link>
        }
      />
    </div>
  );
}
