import { randomUUID } from "node:crypto";
import { readDB, writeDB } from "./db";
import type { Post } from "./types";

export const PAGE_SIZE = 10;

export interface PostListItem extends Post {
  commentCount: number;
}

export interface PostListResult {
  posts: PostListItem[];
  total: number;
  page: number;
  totalPages: number;
}

export async function getPosts(
  query = "",
  page = 1
): Promise<PostListResult> {
  const db = await readDB();
  const q = query.trim().toLowerCase();

  const filtered = q
    ? db.posts.filter(
        (post) =>
          post.title.toLowerCase().includes(q) ||
          post.content.toLowerCase().includes(q) ||
          post.author.toLowerCase().includes(q)
      )
    : db.posts;

  const sorted = [...filtered].sort(
    (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
  );

  const total = sorted.length;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const safePage = Math.min(Math.max(1, page), totalPages);
  const start = (safePage - 1) * PAGE_SIZE;

  const posts = sorted.slice(start, start + PAGE_SIZE).map((post) => ({
    ...post,
    commentCount: db.comments.filter((c) => c.postId === post.id).length,
  }));

  return { posts, total, page: safePage, totalPages };
}

export async function getPostById(id: string): Promise<Post | undefined> {
  const db = await readDB();
  return db.posts.find((post) => post.id === id);
}

export async function incrementViews(id: string): Promise<void> {
  const db = await readDB();
  const post = db.posts.find((p) => p.id === id);
  if (!post) return;
  post.views += 1;
  await writeDB(db);
}

export interface PostInput {
  title: string;
  author: string;
  content: string;
}

export async function createPost(input: PostInput): Promise<Post> {
  const db = await readDB();
  const now = new Date().toISOString();
  const post: Post = {
    id: randomUUID(),
    title: input.title,
    author: input.author,
    content: input.content,
    createdAt: now,
    updatedAt: now,
    views: 0,
  };
  db.posts.push(post);
  await writeDB(db);
  return post;
}

export async function updatePost(
  id: string,
  input: PostInput
): Promise<Post | undefined> {
  const db = await readDB();
  const post = db.posts.find((p) => p.id === id);
  if (!post) return undefined;
  post.title = input.title;
  post.author = input.author;
  post.content = input.content;
  post.updatedAt = new Date().toISOString();
  await writeDB(db);
  return post;
}

export async function deletePost(id: string): Promise<void> {
  const db = await readDB();
  db.posts = db.posts.filter((p) => p.id !== id);
  db.comments = db.comments.filter((c) => c.postId !== id);
  await writeDB(db);
}
