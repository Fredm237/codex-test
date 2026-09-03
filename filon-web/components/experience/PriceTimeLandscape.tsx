"use client";

import { useId, useMemo, useState, type CSSProperties } from "react";
import { money, type CardLocale, type ComparableHistoryPoint } from "@/components/filon/product-copy";

const COPY = {
  fr: {
    title: "Le prix dans le temps",
    intro: "Chaque relief correspond à un relevé comparable réellement conservé.",
    explore: "Explorer les relevés de prix",
    reading: "Relevé sélectionné",
    first: "Premier relevé",
    last: "Dernier relevé",
    list: "Voir tous les relevés",
    date: "Date",
    price: "Prix",
    observations: "relevés comparables",
  },
  nl: {
    title: "De prijs door de tijd",
    intro: "Elk reliëf is een werkelijk bewaarde vergelijkbare meting.",
    explore: "Verken de prijsmetingen",
    reading: "Geselecteerde meting",
    first: "Eerste meting",
    last: "Laatste meting",
    list: "Bekijk alle metingen",
    date: "Datum",
    price: "Prijs",
    observations: "vergelijkbare metingen",
  },
  en: {
    title: "Price through time",
    intro: "Each relief is a comparable reading actually retained by FILON.",
    explore: "Explore price readings",
    reading: "Selected reading",
    first: "First reading",
    last: "Latest reading",
    list: "View every reading",
    date: "Date",
    price: "Price",
    observations: "comparable readings",
  },
} as const;

type Point = ComparableHistoryPoint & { x: number; y: number };

function dateLabel(value: string, locale: CardLocale) {
  const language = locale === "nl" ? "nl-BE" : locale === "en" ? "en-GB" : "fr-BE";
  return new Intl.DateTimeFormat(language, { day: "2-digit", month: "short", year: "numeric" }).format(new Date(value));
}

export function PriceTimeLandscape({
  history,
  currency,
  locale,
}: {
  history: ComparableHistoryPoint[];
  currency: string;
  locale: CardLocale;
}) {
  const titleId = `p19-price-${useId().replace(/:/g, "")}`;
  const C = COPY[locale];
  const [activeIndex, setActiveIndex] = useState(history.length - 1);
  const width = 720;
  const height = 260;
  const padX = 30;
  const padY = 28;
  const points = useMemo<Point[]>(() => {
    const prices = history.map((point) => point.price);
    const min = Math.min(...prices);
    const max = Math.max(...prices);
    const span = max - min || 1;
    const step = (width - padX * 2) / Math.max(history.length - 1, 1);
    return history.map((point, index) => ({
      ...point,
      x: padX + index * step,
      y: height - padY - ((point.price - min) / span) * (height - padY * 2),
    }));
  }, [history]);
  if (points.length < 2) return null;

  const active = points[Math.min(activeIndex, points.length - 1)];
  const line = points.map((point, index) => `${index === 0 ? "M" : "L"} ${point.x} ${point.y}`).join(" ");
  const area = `${line} L ${points.at(-1)!.x} ${height - padY} L ${points[0].x} ${height - padY} Z`;
  const style = { "--p19-history-progress": `${(activeIndex / (points.length - 1)) * 100}%` } as CSSProperties;

  return (
    <section className="p19-price-landscape" data-sticky-cta-avoid aria-labelledby={titleId} style={style}>
      <header className="p19-price-landscape-head">
        <div>
          <p>FILON / PRICE–TIME LANDSCAPE</p>
          <h2 id={titleId}>{C.title}</h2>
        </div>
        <span>{points.length} {C.observations}</span>
      </header>
      <p className="p19-price-landscape-intro">{C.intro}</p>

      <div className="p19-price-landscape-stage">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          role="img"
          aria-label={`${C.title}. ${points.length} ${C.observations}.`}
          preserveAspectRatio="none"
        >
          <defs>
            <linearGradient id={`${titleId}-fill`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0" stopColor="#ff8b68" stopOpacity="0.46" />
              <stop offset="1" stopColor="#ff8b68" stopOpacity="0" />
            </linearGradient>
          </defs>
          <g className="p19-price-landscape-grid" aria-hidden="true">
            <path d={`M ${padX} 60 H ${width - padX}`} />
            <path d={`M ${padX} 130 H ${width - padX}`} />
            <path d={`M ${padX} 200 H ${width - padX}`} />
          </g>
          <path className="p19-price-landscape-area" d={area} fill={`url(#${titleId}-fill)`} />
          <path className="p19-price-landscape-line" d={line} />
          {points.map((point, index) => (
            <circle
              key={`${point.at}-${index}`}
              className={index === activeIndex ? "is-active" : undefined}
              cx={point.x}
              cy={point.y}
              r={index === activeIndex ? 7 : 3.5}
            />
          ))}
        </svg>
        <span className="p19-price-landscape-cursor" aria-hidden="true" />
      </div>

      <div className="p19-price-landscape-control">
        <output aria-live="polite">
          <span>{C.reading}</span>
          <strong>{money(active.price, currency, locale)}</strong>
          <time dateTime={active.at}>{dateLabel(active.at, locale)}</time>
        </output>
        <label>
          <span className="sr-only">{C.explore}</span>
          <input
            type="range"
            min="0"
            max={points.length - 1}
            step="1"
            value={activeIndex}
            aria-label={C.explore}
            onChange={(event) => setActiveIndex(Number(event.currentTarget.value))}
          />
        </label>
        <div className="p19-price-landscape-dates" aria-hidden="true">
          <span>{C.first}</span>
          <span>{C.last}</span>
        </div>
      </div>

      <details className="p19-price-landscape-table">
        <summary>{C.list}</summary>
        <table>
          <thead><tr><th>{C.date}</th><th>{C.price}</th></tr></thead>
          <tbody>
            {points.map((point, index) => (
              <tr key={`${point.at}-row-${index}`}>
                <td><time dateTime={point.at}>{dateLabel(point.at, locale)}</time></td>
                <td>{money(point.price, currency, locale)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </section>
  );
}
