"use client";

import { useActionState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { addCommentAction, type CommentFormState } from "@/lib/actions";

const initialState: CommentFormState = { success: false };

export function CommentForm({ postId }: { postId: string }) {
  const action = addCommentAction.bind(null, postId);
  const [state, formAction, pending] = useActionState(action, initialState);
  const formRef = useRef<HTMLFormElement>(null);

  useEffect(() => {
    if (state.success) {
      formRef.current?.reset();
    }
  }, [state]);

  return (
    <form
      ref={formRef}
      action={formAction}
      className="space-y-3 rounded-lg border p-4"
    >
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-[160px_1fr]">
        <Input name="author" placeholder="이름" required />
        <Textarea name="content" placeholder="댓글을 입력하세요" rows={2} required />
      </div>
      {state.error && <p className="text-sm text-destructive">{state.error}</p>}
      <div className="flex justify-end">
        <Button type="submit" disabled={pending} size="sm">
          {pending ? "등록 중..." : "댓글 등록"}
        </Button>
      </div>
    </form>
  );
}
