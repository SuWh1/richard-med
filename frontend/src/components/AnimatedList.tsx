import { Children, isValidElement, type ReactNode, useRef } from "react";
import { motion, useInView } from "motion/react";

const prefersReducedMotion = () =>
  typeof window !== "undefined" &&
  window.matchMedia("(prefers-reduced-motion: reduce)").matches;

function AnimatedItem({ children, index }: { children: ReactNode; index: number }) {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { amount: 0.3, once: true });
  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, scale: 0.96, y: 8 }}
      animate={inView ? { opacity: 1, scale: 1, y: 0 } : undefined}
      transition={{
        duration: 0.28,
        delay: Math.min(index * 0.05, 0.35),
        ease: "easeOut",
      }}
    >
      {children}
    </motion.div>
  );
}

interface AnimatedListProps {
  children: ReactNode;
  className?: string;
}

/** Reveals its children with a staggered scale + fade as they scroll into view. */
export function AnimatedList({ children, className }: AnimatedListProps) {
  if (prefersReducedMotion()) {
    return <div className={className}>{children}</div>;
  }
  const items = Children.toArray(children);
  return (
    <div className={className}>
      {items.map((child, i) => (
        <AnimatedItem
          key={isValidElement(child) && child.key != null ? child.key : i}
          index={i}
        >
          {child}
        </AnimatedItem>
      ))}
    </div>
  );
}
