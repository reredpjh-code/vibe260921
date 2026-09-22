import { notFound } from "next/navigation";
import { PostForm } from "@/components/post-form";
import { updatePostAction } from "@/lib/actions";
import { getPostById } from "@/lib/posts";

type EditPageProps = {
  params: Promise<{ id: string }>;
};

export default async function EditPostPage({ params }: EditPageProps) {
  const { id } = await params;
  const post = await getPostById(id);
  if (!post) notFound();

  const action = updatePostAction.bind(null, id);

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <h1 className="text-2xl font-bold">글 수정</h1>
      <PostForm action={action} post={post} submitLabel="수정 완료" />
    </div>
  );
}
