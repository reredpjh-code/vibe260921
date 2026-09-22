import { supabase } from "./supabase";
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

interface PostRow {
  id: string;
  title: string;
  author: string;
  content: string;
  views: number;
  created_at: string;
  updated_at: string;
}

function mapPost(row: PostRow): Post {
  return {
    id: row.id,
    title: row.title,
    author: row.author,
    content: row.content,
    createdAt: row.created_at,
    updatedAt: row.updated_at,
    views: row.views,
  };
}

function sanitizeSearchTerm(query: string): string {
  return query.replace(/[,()%_]/g, " ").trim();
}

export async function getPosts(
  query = "",
  page = 1
): Promise<PostListResult> {
  const term = sanitizeSearchTerm(query);
  const searchFilter = term
    ? `title.ilike.%${term}%,author.ilike.%${term}%,content.ilike.%${term}%`
    : null;

  let countQuery = supabase
    .from("posts")
    .select("id", { count: "exact", head: true });
  if (searchFilter) countQuery = countQuery.or(searchFilter);

  const { count, error: countError } = await countQuery;
  if (countError) throw countError;

  const total = count ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const safePage = Math.min(Math.max(1, page), totalPages);
  const start = (safePage - 1) * PAGE_SIZE;
  const end = start + PAGE_SIZE - 1;

  let dataQuery = supabase
    .from("posts")
    .select("*, comments(count)")
    .order("created_at", { ascending: false })
    .range(start, end);
  if (searchFilter) dataQuery = dataQuery.or(searchFilter);

  const { data, error } = await dataQuery;
  if (error) throw error;

  const posts: PostListItem[] = (data ?? []).map((row) => {
    const { comments, ...postRow } = row as PostRow & {
      comments?: { count: number }[];
    };
    return {
      ...mapPost(postRow as PostRow),
      commentCount: comments?.[0]?.count ?? 0,
    };
  });

  return { posts, total, page: safePage, totalPages };
}

export async function getPostById(id: string): Promise<Post | undefined> {
  const { data, error } = await supabase
    .from("posts")
    .select("*")
    .eq("id", id)
    .maybeSingle();
  if (error) throw error;
  return data ? mapPost(data as PostRow) : undefined;
}

export async function incrementViews(id: string): Promise<void> {
  const { error } = await supabase.rpc("increment_post_views", {
    post_id: id,
  });
  if (error) throw error;
}

export interface PostInput {
  title: string;
  author: string;
  content: string;
}

export async function createPost(input: PostInput): Promise<Post> {
  const { data, error } = await supabase
    .from("posts")
    .insert({
      title: input.title,
      author: input.author,
      content: input.content,
    })
    .select()
    .single();
  if (error) throw error;
  return mapPost(data as PostRow);
}

export async function updatePost(
  id: string,
  input: PostInput
): Promise<Post | undefined> {
  const { data, error } = await supabase
    .from("posts")
    .update({
      title: input.title,
      author: input.author,
      content: input.content,
      updated_at: new Date().toISOString(),
    })
    .eq("id", id)
    .select()
    .maybeSingle();
  if (error) throw error;
  return data ? mapPost(data as PostRow) : undefined;
}

export async function deletePost(id: string): Promise<void> {
  const { error } = await supabase.from("posts").delete().eq("id", id);
  if (error) throw error;
}
