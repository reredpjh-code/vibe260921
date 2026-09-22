import Link from "next/link";
import { notFound } from "next/navigation";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { CommentForm } from "@/components/comment-form";
import { DeletePostButton } from "@/components/delete-post-button";
import { deleteCommentAction } from "@/lib/actions";
import { getCommentsByPostId } from "@/lib/comments";
import { formatDate } from "@/lib/format";
import { getPostById, incrementViews } from "@/lib/posts";

export const dynamic = "force-dynamic";

type PostPageProps = {
  params: Promise<{ id: string }>;
};

export default async function PostDetailPage({ params }: PostPageProps) {
  const { id } = await params;
  const post = await getPostById(id);
  if (!post) notFound();

  await incrementViews(id);
  const comments = await getCommentsByPostId(id);

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div className="space-y-3">
        <h1 className="text-2xl font-bold">{post.title}</h1>
        <div className="flex flex-wrap items-center justify-between gap-2 text-sm text-muted-foreground">
          <div className="flex items-center gap-2">
            <Avatar className="h-6 w-6">
              <AvatarFallback className="text-xs">
                {post.author.slice(0, 1)}
              </AvatarFallback>
            </Avatar>
            <span>{post.author}</span>
            <span>·</span>
            <span>{formatDate(post.createdAt)}</span>
          </div>
          <Badge variant="outline">조회 {post.views}</Badge>
        </div>
      </div>

      <Separator />

      <p className="whitespace-pre-wrap leading-relaxed">{post.content}</p>

      <Separator />

      <div className="flex justify-between">
        <Button
          variant="outline"
          nativeButton={false}
          render={<Link href="/board">목록</Link>}
        />
        <div className="flex gap-2">
          <Button
            variant="secondary"
            nativeButton={false}
            render={<Link href={`/board/${post.id}/edit`}>수정</Link>}
          />
          <DeletePostButton postId={post.id} />
        </div>
      </div>

      <Separator />

      <div className="space-y-4">
        <h2 className="font-semibold">댓글 {comments.length}개</h2>
        <div className="space-y-3">
          {comments.map((comment) => (
            <div
              key={comment.id}
              className="flex items-start justify-between gap-3 rounded-lg border p-3"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2 text-sm font-medium">
                  <span>{comment.author}</span>
                  <span className="text-xs font-normal text-muted-foreground">
                    {formatDate(comment.createdAt)}
                  </span>
                </div>
                <p className="text-sm">{comment.content}</p>
              </div>
              <form action={deleteCommentAction.bind(null, post.id, comment.id)}>
                <Button type="submit" variant="ghost" size="sm">
                  삭제
                </Button>
              </form>
            </div>
          ))}
        </div>
        <CommentForm postId={post.id} />
      </div>
    </div>
  );
}
