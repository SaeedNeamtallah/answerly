import Image from "next/image";

export function AnswerlyLogo({ className = "", variant = "dark" }: { className?: string; variant?: "light" | "dark" | string }) {
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <Image
        src="/ANSWERLY.png"
        alt="Answerly Logo"
        width={400}
        height={133}
        priority
        className="h-auto w-full max-w-[400px] object-contain object-left"
      />
    </div>
  );
}
