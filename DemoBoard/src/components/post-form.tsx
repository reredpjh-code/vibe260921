"use client";

import { useActionState, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import type { FormState } from "@/lib/actions";
import type { Post } from "@/lib/types";

type PostFormAction = (
  state: FormState,
  formData: FormData
) => Promise<FormState>;

const initialState: FormState = { success: false };

export function PostForm({
  action,
  post,
  submitLabel,
}: {
  action: PostFormAction;
  post?: Post;
  submitLabel: string;
}) {
  const router = useRouter();
  const [state, formAction, pending] = useActionState(action, initialState);
  const [title, setTitle] = useState(post?.title ?? "");
  const [author, setAuthor] = useState(post?.author ?? "");
  const [content, setContent] = useState(post?.content ?? "");

  useEffect(() => {
    if (state.success && state.id) {
      toast.success("저장되었습니다.");
      router.push(`/board/${state.id}`);
    } else if (state.message) {
      toast.error(state.message);
    }
  }, [state, router]);

  return (
    <form action={formAction} className="space-y-5">
      <div className="space-y-2">
        <Label htmlFor="title">제목</Label>
        <Input
          id="title"
          name="title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="제목을 입력하세요"
          required
        />
        {state.errors?.title && (
          <p className="text-sm text-destructive">{state.errors.title}</p>
        )}
      </div>
      <div className="space-y-2">
        <Label htmlFor="author">작성자</Label>
        <Input
          id="author"
          name="author"
          value={author}
          onChange={(e) => setAuthor(e.target.value)}
          placeholder="이름을 입력하세요"
          required
        />
        {state.errors?.author && (
          <p className="text-sm text-destructive">{state.errors.author}</p>
        )}
      </div>
      <div className="space-y-2">
        <Label htmlFor="content">내용</Label>
        <Textarea
          id="content"
          name="content"
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="내용을 입력하세요"
          rows={12}
          required
        />
        {state.errors?.content && (
          <p className="text-sm text-destructive">{state.errors.content}</p>
        )}
      </div>
      <div className="flex justify-end gap-2">
        <Button type="button" variant="outline" onClick={() => router.back()}>
          취소
        </Button>
        <Button type="submit" disabled={pending}>
          {pending ? "저장 중..." : submitLabel}
        </Button>
      </div>
    </form>
  );
}
