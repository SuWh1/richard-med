import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { FreshBadge } from "./FreshBadge";

describe("FreshBadge", () => {
  it("should show the stale-warning label for a stale price", () => {
    render(<FreshBadge freshness="stale" ageDays={45} />);
    expect(screen.getByText("Цена требует обновления")).toBeInTheDocument();
  });

  it("should show 'today' for a fresh zero-day-old price", () => {
    render(<FreshBadge freshness="fresh" ageDays={0} />);
    expect(screen.getByText("Обновлено сегодня")).toBeInTheDocument();
  });

  it("should show the day count for a recent price", () => {
    render(<FreshBadge freshness="recent" ageDays={5} />);
    expect(screen.getByText("Обновлено 5 дн. назад")).toBeInTheDocument();
  });
});
