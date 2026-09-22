import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function SearchForm({ defaultValue }: { defaultValue?: string }) {
  return (
    <form action="/board" className="flex gap-2">
      <Input
        name="q"
        defaultValue={defaultValue}
        placeholder="제목, 작성자, 내용 검색"
        className="max-w-sm"
      />
      <Button type="submit" variant="secondary">
        검색
      </Button>
    </form>
  );
}
