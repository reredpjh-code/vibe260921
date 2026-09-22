import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import type { Comment, Post } from "./types";

interface Database {
  posts: Post[];
  comments: Comment[];
}

const DATA_DIR = path.join(process.cwd(), "data");
const DB_PATH = path.join(DATA_DIR, "db.json");

const seedData: Database = {
  posts: [
    {
      id: "1",
      title: "DemoBoard에 오신 것을 환영합니다",
      author: "관리자",
      content:
        "DemoBoard는 Next.js, TypeScript, shadcn/ui로 만든 게시판 데모입니다.\n\n상단의 글쓰기 버튼을 눌러 새 글을 작성해보세요.",
      createdAt: "2026-09-15T09:00:00.000Z",
      updatedAt: "2026-09-15T09:00:00.000Z",
      views: 12,
    },
    {
      id: "2",
      title: "shadcn/ui 컴포넌트 사용 예시",
      author: "홍길동",
      content:
        "Button, Card, Table, Dialog 등 shadcn/ui 컴포넌트를 활용해 게시판 UI를 구성했습니다.\n\n필요한 컴포넌트는 npx shadcn@latest add <component> 명령으로 추가할 수 있습니다.",
      createdAt: "2026-09-18T03:30:00.000Z",
      updatedAt: "2026-09-18T03:30:00.000Z",
      views: 5,
    },
  ],
  comments: [
    {
      id: "c1",
      postId: "1",
      author: "방문자",
      content: "깔끔한 게시판이네요!",
      createdAt: "2026-09-16T10:00:00.000Z",
    },
  ],
};

async function ensureDB(): Promise<void> {
  await mkdir(DATA_DIR, { recursive: true });
  try {
    await readFile(DB_PATH, "utf-8");
  } catch {
    await writeFile(DB_PATH, JSON.stringify(seedData, null, 2), "utf-8");
  }
}

export async function readDB(): Promise<Database> {
  await ensureDB();
  const raw = await readFile(DB_PATH, "utf-8");
  return JSON.parse(raw) as Database;
}

export async function writeDB(data: Database): Promise<void> {
  await mkdir(DATA_DIR, { recursive: true });
  await writeFile(DB_PATH, JSON.stringify(data, null, 2), "utf-8");
}
