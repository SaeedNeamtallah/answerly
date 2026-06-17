import { AnimatedAuthBranding } from "@/components/shared/AnimatedAuthBranding";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen">
      {/* Left Pane - Branding (hidden on small screens) */}
      <div className="hidden w-1/2 flex-col justify-center bg-gradient-to-br from-[#F0F5FA] to-[#E2EAF4] p-12 lg:flex">
        <AnimatedAuthBranding />
      </div>

      {/* Right Pane - Auth Forms */}
      <div className="flex w-full flex-col items-center justify-center bg-slate-50 p-4 lg:w-1/2 lg:bg-white">
        {children}
      </div>
    </div>
  );
}
