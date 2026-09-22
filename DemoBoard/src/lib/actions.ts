"use server";

import { revalidatePath } from "next/cache";
import * as comments from "./comments";
import * as posts from "./posts";

export interface FormState {
  success: boolean;
  message?: string;
  errors?: Record<string, string>;
  id?: string;
}

function validatePostInput(formData: FormData) {
  const title = String(formData.get("title") ?? "").trim();
  const author = String(formData.get("author") ?? "").trim();
  const content = String(formData.get("content") ?? "").trim();

  const errors: Record<string, string> = {};
  if (!title) errors.title = "제목을 입력해주세요.";
  if (!author) errors.author = "작성자를 입력해주세요.";
  if (!content) errors.content = "내용을 입력해주세요.";

  return { title, author, content, errors };
}

export async function createPostAction(
  _prevState: FormState,
  formData: FormData
): Promise<FormState> {
  const { title, author, content, errors } = validatePostInput(formData);
  if (Object.keys(errors).length > 0) {
    return { success: false, errors };
  }

  const post = await posts.createPost({ title, author, content });
  revalidatePath("/board");
  return { success: true, id: post.id };
}

export async function updatePostAction(
  id: string,
  _prevState: FormState,
  formData: FormData
): Promise<FormState> {
  const { title, author, content, errors } = validatePostInput(formData);
  if (Object.keys(errors).length > 0) {
    return { success: false, errors };
  }

  const post = await posts.updatePost(id, { title, author, content });
  if (!post) {
    return { success: false, message: "게시글을 찾을 수 없습니다." };
  }

  revalidatePath("/board");
  revalidatePath(`/board/${id}`);
  return { success: true, id: post.id };
}

export async function deletePostAction(id: string): Promise<void> {
  await posts.deletePost(id);
  revalidatePath("/board");
}

export interface CommentFormState {
  success: boolean;
  error?: string;
}

export async function addCommentAction(
  postId: string,
  _prevState: CommentFormState,
  formData: FormData
): Promise<CommentFormState> {
  const author = String(formData.get("author") ?? "").trim();
  const content = String(formData.get("content") ?? "").trim();

  if (!author || !content) {
    return { success: false, error: "이름과 내용을 모두 입력해주세요." };
  }

  await comments.addComment({ postId, author, content });
  revalidatePath(`/board/${postId}`);
  return { success: true };
}

export async function deleteCommentAction(
  postId: string,
  commentId: string
): Promise<void> {
  await comments.deleteComment(commentId);
  revalidatePath(`/board/${postId}`);
}
