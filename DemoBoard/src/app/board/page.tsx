import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { BoardPagination } from "@/components/board-pagination";
import { SearchForm } from "@/components/search-form";
import { formatDate } from "@/lib/format";
import { getPosts, PAGE_SIZE } from "@/lib/posts";

export const dynamic = "force-dynamic";

type BoardPageProps = {
  searchParams: Promise<{ q?: string; page?: string }>;
};

export default async function BoardPage({ searchParams }: BoardPageProps) {
  const { q, page } = await searchParams;
  const currentPage = Number(page) || 1;
  const {
    posts,
    total,
    page: safePage,
    totalPages,
  } = await getPosts(q ?? "", currentPage);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">게시판</h1>
          <p className="text-sm text-muted-foreground">전체 {total}개의 글</p>
        </div>
        <Button nativeButton={false} render={<Link href="/board/new">글쓰기</Link>} />
      </div>

      <SearchForm defaultValue={q} />

      <div className="rounded-lg border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-16 text-center">번호</TableHead>
              <TableHead>제목</TableHead>
              <TableHead className="w-32">작성자</TableHead>
              <TableHead className="w-28">작성일</TableHead>
              <TableHead className="w-20 text-right">조회수</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {posts.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={5}
                  className="h-24 text-center text-muted-foreground"
                >
                  게시글이 없습니다.
                </TableCell>
              </TableRow>
            ) : (
              posts.map((post, index) => (
                <TableRow key={post.id}>
                  <TableCell className="text-center text-muted-foreground">
                    {total - ((safePage - 1) * PAGE_SIZE + index)}
                  </TableCell>
                  <TableCell>
                    <Link href={`/board/${post.id}`} className="hover:underline">
                      {post.title}
                    </Link>
                    {post.commentCount > 0 && (
                      <Badge variant="secondary" className="ml-2">
                        {post.commentCount}
                      </Badge>
                    )}
                  </TableCell>
                  <TableCell>{post.author}</TableCell>
                  <TableCell>{formatDate(post.createdAt)}</TableCell>
                  <TableCell className="text-right">{post.views}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      <BoardPagination page={safePage} totalPages={totalPages} query={q} />
    </div>
  );
}
