export function formatRating(rating: number): string {
  return rating.toFixed(1);
}

export function formatReviewCount(count: number): string {
  if (count < 1000) return String(count);
  const thousands = (count / 1000).toFixed(1).replace(".", ",");
  return `${thousands} тыс.`;
}

function pluralRu(count: number, forms: readonly [string, string, string]): string {
  const mod100 = count % 100;
  if (mod100 >= 11 && mod100 <= 14) return forms[2];
  const mod10 = count % 10;
  if (mod10 === 1) return forms[0];
  if (mod10 >= 2 && mod10 <= 4) return forms[1];
  return forms[2];
}

export function reviewWord(count: number): string {
  return pluralRu(count, ["отзыв", "отзыва", "отзывов"]);
}

export function pointWord(count: number): string {
  return pluralRu(count, ["точка", "точки", "точек"]);
}
