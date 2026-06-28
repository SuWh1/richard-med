export function BrandPanel() {
  return (
    <div className="relative hidden md:block">
      <div className="flex h-full items-center justify-center bg-gradient-to-br from-primary to-primary-hover p-10">
        <img
          src="/richard-without-background.png"
          alt=""
          className="w-3/4 max-w-[260px] object-contain drop-shadow-lg"
        />
      </div>
    </div>
  );
}
