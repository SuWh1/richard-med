import { useCallback, useEffect, useState } from "react";

export const MAX_COMPARE = 3;

interface CompareSelection {
  selected: number[];
  isSelected: (clinicId: number) => boolean;
  toggle: (clinicId: number) => void;
  clear: () => void;
  isFull: boolean;
}

export function useCompareSelection(serviceId: number | null): CompareSelection {
  const [selected, setSelected] = useState<number[]>([]);

  useEffect(() => {
    setSelected([]);
  }, [serviceId]);

  const toggle = useCallback((clinicId: number) => {
    setSelected((prev) => {
      if (prev.includes(clinicId)) return prev.filter((id) => id !== clinicId);
      if (prev.length >= MAX_COMPARE) return prev;
      return [...prev, clinicId];
    });
  }, []);

  const clear = useCallback(() => setSelected([]), []);
  const isSelected = useCallback(
    (clinicId: number) => selected.includes(clinicId),
    [selected],
  );

  return { selected, isSelected, toggle, clear, isFull: selected.length >= MAX_COMPARE };
}
