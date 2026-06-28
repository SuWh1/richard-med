import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { ClinicReview } from "@/types";
import { ReviewItem } from "./ReviewItem";

const review: ClinicReview = {
  id: 1,
  author: "Айжан Ахметова",
  rating: 5,
  text: "Приятный и вежливый персонал, в помещении чисто",
  official_answer: null,
  review_date: "2026-04-26",
  source: "2gis",
  branch_id: 3,
  city: "Астана",
};

describe("ReviewItem", () => {
  it("should render author and review text", () => {
    render(<ReviewItem review={review} />);
    expect(screen.getByText("Айжан Ахметова")).toBeInTheDocument();
    expect(screen.getByText(/вежливый персонал/)).toBeInTheDocument();
  });

  it("should expose the star rating accessibly", () => {
    render(<ReviewItem review={review} />);
    expect(screen.getByLabelText(/Оценка 5 из 5/)).toBeInTheDocument();
  });

  it("should render the clinic's official answer when present", () => {
    render(
      <ReviewItem review={{ ...review, official_answer: "Спасибо за отзыв!" }} />,
    );
    expect(screen.getByText("Ответ клиники")).toBeInTheDocument();
    expect(screen.getByText("Спасибо за отзыв!")).toBeInTheDocument();
  });

  it("should fall back to an anonymous label when author is missing", () => {
    render(<ReviewItem review={{ ...review, author: null }} />);
    expect(screen.getByText("Гость")).toBeInTheDocument();
  });
});
