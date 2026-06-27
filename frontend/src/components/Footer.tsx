export function Footer() {
  return (
    <footer className="mt-auto border-t border-border bg-white py-5">
      <div className="mx-auto max-w-6xl px-5 text-center">
        <p className="text-xs text-muted-foreground">
          Информация о ценах носит справочный характер. Перед лечением обратитесь к
          врачу.
        </p>
        <p className="mt-1 text-[11px] text-faintest">
          © {new Date().getFullYear()} Richard Med · Все права защищены
        </p>
      </div>
    </footer>
  );
}
