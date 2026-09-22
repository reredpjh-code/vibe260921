import { randomUUID } from "node:crypto";
import { readDB, writeDB } from "./db";
import type { Comment } from "./types";

export async function getCommentsByPostId(postId: string): Promise<Comment[]> {
  const db = await readDB();
  return db.comments
    .filter((c) => c.postId === postId)
    .sort(
      (a, b) => new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime()
    );
}

export interface CommentInput {
  postId: string;
  author: string;
  content: string;
}

export async function addComment(input: CommentInput): Promise<Comment> {
  const db = await readDB();
  const comment: Comment = {
    id: randomUUID(),
    postId: input.postId,
    author: input.author,
    content: input.content,
    createdAt: new Date().toISOString(),
  };
  db.comments.push(comment);
  await writeDB(db);
  return comment;
}

export async function deleteComment(id: string): Promise<void> {
  const db = await readDB();
  db.comments = db.comments.filter((c) => c.id !== id);
  await writeDB(db);
}
