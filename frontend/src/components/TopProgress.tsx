import { useEffect, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import { useIsFetching } from "@tanstack/react-query";

/** Thin top bar that sweeps on route change and while data is fetching —
 *  perceived "loading" without ever blocking the (instant) DB-backed render.
 *  Always completes + hides: on fetch finish, or (cached nav) after a short pulse. */
export function TopProgress() {
  const { pathname } = useLocation();
  const fetching = useIsFetching();
  const [width, setWidth] = useState(0);
  const [show, setShow] = useState(false);
  const fetchingRef = useRef(fetching);
  fetchingRef.current = fetching;

  const finish = (setW: typeof setWidth, setS: typeof setShow) => {
    setW(100);
    const hide = window.setTimeout(() => setS(false), 250);
    const reset = window.setTimeout(() => setW(0), 500);
    return () => {
      clearTimeout(hide);
      clearTimeout(reset);
    };
  };

  // Route change → start a pulse; if nothing is fetching, finish it on its own.
  useEffect(() => {
    setShow(true);
    setWidth(10);
    const creep = window.setTimeout(() => setWidth((w) => Math.max(w, 80)), 50);
    const check = window.setTimeout(() => {
      if (fetchingRef.current === 0) finish(setWidth, setShow);
    }, 450);
    return () => {
      clearTimeout(creep);
      clearTimeout(check);
    };
  }, [pathname]);

  // While fetching → creep + hold near the end; when it settles → complete + hide.
  useEffect(() => {
    if (fetching > 0) {
      setShow(true);
      setWidth((w) => Math.max(w, 80));
      return;
    }
    return finish(setWidth, setShow);
  }, [fetching]);

  return (
    <div className="pointer-events-none fixed inset-x-0 top-0 z-[100] h-[3px]">
      <div
        className="h-full rounded-r-full bg-primary shadow-[0_0_8px_var(--primary)]"
        style={{
          width: `${width}%`,
          opacity: show ? 1 : 0,
          transition: "width 300ms ease-out, opacity 220ms ease-out",
        }}
      />
    </div>
  );
}
