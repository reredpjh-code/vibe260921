import { PostForm } from "@/components/post-form";
import { createPostAction } from "@/lib/actions";

export default function NewPostPage() {
  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <h1 className="text-2xl font-bold">글쓰기</h1>
      <PostForm action={createPostAction} submitLabel="등록" />
    </div>
  );
}
