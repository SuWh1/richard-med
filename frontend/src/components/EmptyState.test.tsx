import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { EmptyState } from "./EmptyState";

describe("EmptyState", () => {
  it("should show other cities and switch city from the hint", async () => {
    const onPickCity = vi.fn();
    render(
      <EmptyState
        query="Консультация пульмонолога"
        suggestions={[]}
        currentCity="Астана"
        otherCities={[{ name: "Караганда", count: 1 }]}
        onPickCity={onPickCity}
        onPickSuggestion={() => {}}
      />,
    );

    expect(screen.getByText("В городе Астана свежих цен нет")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Караганда · 1" }));

    expect(onPickCity).toHaveBeenCalledWith("Караганда");
  });
});
