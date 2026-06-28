export const KDL_CITY_SLUG: Record<string, string> = {
  Астана: "astana",
  Алматы: "almaty",
  Шымкент: "shymkent",
  Караганда: "karaganda",
  Актобе: "aktobe",
  Тараз: "taraz",
  Павлодар: "pavlodar",
  "Усть-Каменогорск": "ust-kamenogorsk",
  Атырау: "atyrau",
  Костанай: "kostanay",
  Кызылорда: "kyzylorda",
  Актау: "aktau",
  Кокшетау: "kokshetau",
  Туркестан: "turkestan",
  Темиртау: "temirtau",
  Экибастуз: "ekibastuz",
  Петропавловск: "petropavlovsk",
};

const INVITRO_PRICE_PAGE = "https://invitro.kz/analizes/for-doctors/";

export function sourceViewUrl(
  sourceUrl: string,
  city: string | null,
  serviceName: string,
): string {
  let host: string;
  try {
    host = new URL(sourceUrl).hostname;
  } catch {
    return sourceUrl;
  }

  if (host.includes("kdlolymp")) {
    const slug = (city && KDL_CITY_SLUG[city]) || "astana";
    const qs = new URLSearchParams({ search: serviceName });
    return `https://kdlolymp.kz/pricelist/${slug}?${qs.toString()}`;
  }

  if (host.includes("invitro")) {
    return INVITRO_PRICE_PAGE;
  }

  return sourceUrl;
}
