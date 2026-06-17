"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { useAuthStore } from "@/store/auth-store";
import { apiRequest } from "@/lib/api/client";
import { Loader2, ShieldCheck, Copy, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

interface MFASetupResponse {
  secret: string;
  provisioning_uri: string;
  qr_code_svg: string;
}

interface MFAVerifyResponse {
  success: boolean;
  recovery_codes: string[];
}

export default function MFASetupPage() {
  const router = useRouter();
  const accessToken = useAuthStore((state) => state.accessToken);
  const [setupData, setSetupData] = useState<MFASetupResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [verifying, setVerifying] = useState(false);
  const [token, setToken] = useState("");
  const [recoveryCodes, setRecoveryCodes] = useState<string[] | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!accessToken) {
      router.push("/login");
      return;
    }

    apiRequest<MFASetupResponse>("/auth/mfa/setup")
      .then((data) => {
        setSetupData(data);
        setLoading(false);
      })
      .catch((err) => {
        toast.error("Failed to initialize MFA setup");
        setLoading(false);
      });
  }, [accessToken, router]);

  const handleVerify = async () => {
    if (!token) return;
    setVerifying(true);
    try {
      const res = await apiRequest<MFAVerifyResponse>("/auth/mfa/verify", {
        method: "POST",
        body: JSON.stringify({ token }),
      });
      if (res.success) {
        toast.success("MFA setup successfully!");
        setRecoveryCodes(res.recovery_codes);
      }
    } catch (err: any) {
      toast.error(err.message || "Invalid MFA token");
    } finally {
      setVerifying(false);
    }
  };

  const copyCodes = () => {
    if (!recoveryCodes) return;
    navigator.clipboard.writeText(recoveryCodes.join("\n"));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    toast.success("Recovery codes copied to clipboard");
  };

  if (loading) {
    return (
      <div className="flex h-screen w-full items-center justify-center">
        <Loader2 className="size-8 animate-spin text-primary" />
      </div>
    );
  }

  if (recoveryCodes) {
    return (
      <div className="w-full max-w-md">
        <Card className="border-0 shadow-xl lg:border-border/50 lg:shadow-2xl">
          <CardHeader className="space-y-4 px-8 pt-8">
            <div className="flex justify-center">
              <div className="flex size-12 items-center justify-center rounded-full bg-green-100">
                <ShieldCheck className="size-6 text-green-600" />
              </div>
            </div>
            <div className="text-center">
              <CardTitle className="text-2xl">MFA Enabled</CardTitle>
              <CardDescription>
                Save these recovery codes in a secure place. They can be used to access your account if you lose your authenticator device.
              </CardDescription>
            </div>
          </CardHeader>
          <CardContent className="px-8 pb-8 space-y-6">
            <div className="rounded-md bg-muted p-4 font-mono text-sm">
              <div className="grid grid-cols-2 gap-2">
                {recoveryCodes.map((code, i) => (
                  <div key={i} className="text-center">{code}</div>
                ))}
              </div>
            </div>
            <Button onClick={copyCodes} variant="outline" className="w-full">
              {copied ? <Check className="mr-2 size-4" /> : <Copy className="mr-2 size-4" />}
              {copied ? "Copied" : "Copy Codes"}
            </Button>
            <Button onClick={() => router.push("/dashboard")} className="w-full bg-blue-600 hover:bg-blue-700">
              Continue to Dashboard
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="w-full max-w-md">
      <Card className="border-0 shadow-xl lg:border-border/50 lg:shadow-2xl">
        <CardHeader className="space-y-4 px-8 pt-8">
          <div className="text-center">
            <CardTitle className="text-2xl text-[#162758]">Set up MFA</CardTitle>
            <CardDescription>
              Scan the QR code with your authenticator app (like Google Authenticator or Authy) to generate a code.
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent className="px-8 pb-8 space-y-6">
          {setupData && (
            <div className="flex flex-col items-center space-y-4">
              <div 
                className="bg-white p-2 rounded-lg"
                dangerouslySetInnerHTML={{ __html: setupData.qr_code_svg }}
                style={{ width: "200px", height: "200px" }}
              />
              <div className="text-center">
                <p className="text-sm font-medium">Or enter code manually:</p>
                <p className="font-mono text-sm tracking-wider text-muted-foreground mt-1">
                  {setupData.secret}
                </p>
              </div>
            </div>
          )}

          <div className="space-y-1.5 pt-4 border-t">
            <label className="text-sm font-medium text-slate-700">6-digit Code</label>
            <Input
              placeholder="123456"
              className="h-11 text-center font-mono tracking-widest text-lg"
              value={token}
              onChange={(e) => setToken(e.target.value.replace(/\D/g, "").slice(0, 6))}
            />
          </div>

          <Button 
            onClick={handleVerify} 
            disabled={verifying || token.length !== 6}
            className="h-11 w-full rounded-lg bg-blue-600 hover:bg-blue-700"
          >
            {verifying ? <Loader2 className="mr-2 size-4 animate-spin" /> : null}
            Verify and Enable
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
