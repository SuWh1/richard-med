import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AnimatedList } from "./AnimatedList";

function setReducedMotion(reduce: boolean) {
  window.matchMedia = vi.fn().mockImplementation((query: string) => ({
    matches: reduce,
    media: query,
    onchange: null,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    addListener: vi.fn(),
    removeListener: vi.fn(),
    dispatchEvent: vi.fn(),
  }));
}

describe("AnimatedList", () => {
  beforeEach(() => setReducedMotion(false));

  it("should render all provided items", () => {
    render(
      <AnimatedList>
        <div>Альфа</div>
        <div>Бета</div>
        <div>Гамма</div>
      </AnimatedList>,
    );
    expect(screen.getByText("Альфа")).toBeInTheDocument();
    expect(screen.getByText("Бета")).toBeInTheDocument();
    expect(screen.getByText("Гамма")).toBeInTheDocument();
  });

  it("should apply the container className", () => {
    const { container } = render(
      <AnimatedList className="space-y-3">
        <div>X</div>
      </AnimatedList>,
    );
    expect(container.firstChild).toHaveClass("space-y-3");
  });

  it("should still render every child under reduced motion", () => {
    setReducedMotion(true);
    render(
      <AnimatedList>
        <div>Один</div>
        <div>Два</div>
      </AnimatedList>,
    );
    expect(screen.getByText("Один")).toBeInTheDocument();
    expect(screen.getByText("Два")).toBeInTheDocument();
  });
});
