-- DemoBoard schema
-- Run this once in the Supabase project's SQL Editor (Dashboard → SQL Editor → New query).

create extension if not exists pgcrypto;

create table if not exists posts (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  author text not null,
  content text not null,
  views integer not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists comments (
  id uuid primary key default gen_random_uuid(),
  post_id uuid not null references posts (id) on delete cascade,
  author text not null,
  content text not null,
  created_at timestamptz not null default now()
);

create index if not exists comments_post_id_idx on comments (post_id);

-- Atomic view counter (avoids read-then-write races).
create or replace function increment_post_views(post_id uuid)
returns void
language sql
as $$
  update posts set views = views + 1 where id = post_id;
$$;

-- This demo has no authentication, so RLS policies allow public access.
-- Tighten these (e.g. require an authenticated role) before using this in production.
alter table posts enable row level security;
alter table comments enable row level security;

drop policy if exists "Public can read posts" on posts;
create policy "Public can read posts" on posts for select using (true);

drop policy if exists "Public can insert posts" on posts;
create policy "Public can insert posts" on posts for insert with check (true);

drop policy if exists "Public can update posts" on posts;
create policy "Public can update posts" on posts for update using (true) with check (true);

drop policy if exists "Public can delete posts" on posts;
create policy "Public can delete posts" on posts for delete using (true);

drop policy if exists "Public can read comments" on comments;
create policy "Public can read comments" on comments for select using (true);

drop policy if exists "Public can insert comments" on comments;
create policy "Public can insert comments" on comments for insert with check (true);

drop policy if exists "Public can delete comments" on comments;
create policy "Public can delete comments" on comments for delete using (true);

-- Seed data (safe to re-run: fixed ids are upserted).
insert into posts (id, title, author, content, views, created_at, updated_at) values
  (
    '11111111-1111-1111-1111-111111111111',
    'DemoBoard에 오신 것을 환영합니다',
    '관리자',
    'DemoBoard는 Next.js, TypeScript, shadcn/ui, Supabase로 만든 게시판 데모입니다.' || chr(10) || chr(10) || '상단의 글쓰기 버튼을 눌러 새 글을 작성해보세요.',
    12,
    '2026-09-15T09:00:00.000Z',
    '2026-09-15T09:00:00.000Z'
  ),
  (
    '22222222-2222-2222-2222-222222222222',
    'shadcn/ui 컴포넌트 사용 예시',
    '홍길동',
    'Button, Card, Table, Dialog 등 shadcn/ui 컴포넌트를 활용해 게시판 UI를 구성했습니다.' || chr(10) || chr(10) || '필요한 컴포넌트는 npx shadcn@latest add <component> 명령으로 추가할 수 있습니다.',
    5,
    '2026-09-18T03:30:00.000Z',
    '2026-09-18T03:30:00.000Z'
  )
on conflict (id) do nothing;

insert into comments (id, post_id, author, content, created_at) values
  (
    'c1111111-1111-1111-1111-111111111111',
    '11111111-1111-1111-1111-111111111111',
    '방문자',
    '깔끔한 게시판이네요!',
    '2026-09-16T10:00:00.000Z'
  )
on conflict (id) do nothing;
