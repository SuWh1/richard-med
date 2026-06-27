import { Link } from "react-router-dom";
import { MapPin } from "lucide-react";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface HeaderProps {
  city: string;
  onCityChange: (city: string) => void;
  cities: string[];
}

export function Header({ city, onCityChange, cities }: HeaderProps) {
  return (
    <header className="sticky top-0 z-50 flex h-14 items-center border-b border-border bg-white">
      <div className="mx-auto flex w-full max-w-6xl items-center gap-4 px-5">
        <Link to="/" className="flex shrink-0 items-center gap-2">
          <img
            src="/richard-without-background.png"
            alt="Richard Med"
            className="h-9 w-auto object-contain"
          />
          <span className="text-[15px] font-semibold tracking-tight text-foreground">
            Richard Med
          </span>
        </Link>

        <div className="flex-1" />

        <Select value={city} onValueChange={onCityChange}>
          <SelectTrigger className="h-9 w-[170px] gap-1.5 border-transparent text-muted-foreground hover:bg-secondary">
            <MapPin className="h-3.5 w-3.5 text-primary" />
            <SelectValue />
          </SelectTrigger>
          <SelectContent className="max-h-72">
            {cities.map((c) => (
              <SelectItem key={c} value={c}>
                {c}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <nav className="flex items-center gap-1 text-sm text-muted-foreground">
          <Link to="/analytics" className="rounded-lg px-3 py-1.5 hover:bg-secondary">
            Аналитика
          </Link>
          <Link to="/dashboard" className="rounded-lg px-3 py-1.5 hover:bg-secondary">
            Кабинет
          </Link>
        </nav>
      </div>
    </header>
  );
}
