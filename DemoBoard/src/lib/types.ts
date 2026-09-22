export interface Post {
  id: string;
  title: string;
  author: string;
  content: string;
  createdAt: string;
  updatedAt: string;
  views: number;
}

export interface Comment {
  id: string;
  postId: string;
  author: string;
  content: string;
  createdAt: string;
}
