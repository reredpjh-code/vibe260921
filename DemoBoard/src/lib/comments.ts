import { supabase } from "./supabase";
import type { Comment } from "./types";

interface CommentRow {
  id: string;
  post_id: string;
  author: string;
  content: string;
  created_at: string;
}

function mapComment(row: CommentRow): Comment {
  return {
    id: row.id,
    postId: row.post_id,
    author: row.author,
    content: row.content,
    createdAt: row.created_at,
  };
}

export async function getCommentsByPostId(postId: string): Promise<Comment[]> {
  const { data, error } = await supabase
    .from("comments")
    .select("*")
    .eq("post_id", postId)
    .order("created_at", { ascending: true });
  if (error) throw error;
  return (data ?? []).map((row) => mapComment(row as CommentRow));
}

export interface CommentInput {
  postId: string;
  author: string;
  content: string;
}

export async function addComment(input: CommentInput): Promise<Comment> {
  const { data, error } = await supabase
    .from("comments")
    .insert({
      post_id: input.postId,
      author: input.author,
      content: input.content,
    })
    .select()
    .single();
  if (error) throw error;
  return mapComment(data as CommentRow);
}

export async function deleteComment(id: string): Promise<void> {
  const { error } = await supabase.from("comments").delete().eq("id", id);
  if (error) throw error;
}
