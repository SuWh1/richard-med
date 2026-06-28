export function BrandPanel() {
  return (
    <div className="relative hidden md:block">
      <div className="flex h-full flex-col items-center justify-center gap-4 bg-gradient-to-br from-primary to-primary-hover p-10 text-center text-primary-foreground">
        <img
          src="/richard-without-background.png"
          alt=""
          className="h-16 w-16 object-contain drop-shadow"
        />
        <div className="text-xl font-bold">Richard Med</div>
        <p className="max-w-[22ch] text-sm text-primary-foreground/85">
          Цены на медуслуги в одном месте — сравните клиники рядом, с источником и
          картой.
        </p>
      </div>
    </div>
  );
}
