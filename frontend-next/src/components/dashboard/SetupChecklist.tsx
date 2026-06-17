import Link from "next/link";
import { ArrowRight, CheckCircle2, Circle, CircleDashed, Users, Settings, PhoneForwarded, BarChart3, Bot, BookOpen } from "lucide-react";

import { BotIntegration } from "@/lib/types/bot";
import { Conversation } from "@/lib/types/conversation";
import { Project } from "@/lib/types/project";

import { Button } from "@/components/ui/button";

export function SetupChecklist({
  projects = [],
  bots = [],
  conversations = [],
}: {
  projects?: Project[];
  bots?: BotIntegration[];
  conversations?: Conversation[];
}) {
  const hasProject = projects.length > 0;
  const hasBot = bots.length > 0;
  
  const getStatus = (isCompleted: boolean, isCurrent: boolean) => {
    if (isCompleted) return "completed";
    if (isCurrent) return "current";
    return "pending";
  };

  const steps = [
    { 
      label: "Create your first knowledge base", 
      description: "Upload docs and preprocess with ease.",
      href: "/knowledge-bases", 
      icon: <BookOpen className="size-4 text-blue-500" />,
      bg: "bg-blue-50",
      status: getStatus(hasProject, !hasProject) 
    },
    { 
      label: "Connect a Telegram bot", 
      description: "Link your bot and configure webhook.",
      href: "/telegram-bots", 
      icon: <Bot className="size-4 text-blue-500" />,
      bg: "bg-blue-50",
      status: getStatus(hasBot, hasProject && !hasBot) 
    },
    { 
      label: "Add team members", 
      description: "Invite your colleagues to collaborate.",
      href: "/admin/users", 
      icon: <Users className="size-4 text-indigo-500" />,
      bg: "bg-indigo-50",
      status: getStatus(false, hasProject && hasBot) 
    },
    { 
      label: "Configure bot behavior", 
      description: "Set personas, tone, and response rules.",
      href: "/ai-settings", 
      icon: <Settings className="size-4 text-slate-500" />,
      bg: "bg-slate-100",
      status: "pending" 
    },
    { 
      label: "Set up human handoff", 
      description: "Route complex cases to your team.",
      href: "/admin/conversations", 
      icon: <PhoneForwarded className="size-4 text-slate-500" />,
      bg: "bg-slate-100",
      status: "pending" 
    },
    { 
      label: "Review analytics", 
      description: "Track performance and optimize.",
      href: "/admin/stats", 
      icon: <BarChart3 className="size-4 text-slate-500" />,
      bg: "bg-slate-100",
      status: "pending" 
    },
  ];

  const completed = steps.filter((step) => step.status === "completed").length;

  return (
    <div className="flex flex-col rounded-2xl border border-slate-100 bg-white shadow-[0_2px_10px_rgba(0,0,0,0.02)]">
      <div className="flex items-start justify-between border-b border-slate-100 p-6">
        <div className="flex flex-col gap-1">
          <h3 className="text-lg font-semibold text-slate-900">Setup Checklist</h3>
          <p className="text-sm text-slate-500">Follow these steps to get the most out of Answerly.</p>
        </div>
        <div className="flex items-center rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-600">
          {completed} / {steps.length} completed
        </div>
      </div>
      
      <div className="flex flex-col p-2">
        {steps.map((step, idx) => (
          <div key={idx} className="flex items-center justify-between p-4 hover:bg-slate-50 rounded-xl transition-colors">
            <div className="flex items-start gap-4">
              <div className="mt-1">
                {step.status === "completed" ? (
                  <CheckCircle2 className="size-5 text-blue-600 fill-blue-600 bg-white rounded-full" />
                ) : step.status === "current" ? (
                  <CircleDashed className="size-5 text-blue-600" />
                ) : (
                  <Circle className="size-5 text-slate-300" />
                )}
              </div>
              
              <div className={`flex size-10 items-center justify-center rounded-xl ${step.bg}`}>
                {step.icon}
              </div>
              
              <div className="flex flex-col">
                <span className={`text-sm font-semibold ${step.status === 'completed' ? 'text-slate-900 line-through decoration-slate-300 decoration-1' : 'text-slate-900'}`}>
                  {step.label}
                </span>
                <span className="text-sm text-slate-500">{step.description}</span>
              </div>
            </div>
            
            <div className="ml-4 flex-shrink-0">
              {step.status === "completed" ? (
                <span className="text-sm font-medium text-emerald-600">Completed</span>
              ) : step.status === "current" ? (
                <Button className="rounded-full bg-blue-600 hover:bg-blue-700 text-white shadow-sm" size="sm" asChild>
                  <Link href={step.href}>
                    Continue
                  </Link>
                </Button>
              ) : (
                <Button variant="outline" className="rounded-full border-slate-200 text-slate-600" size="sm" asChild>
                  <Link href={step.href}>
                    Go to settings
                  </Link>
                </Button>
              )}
            </div>
          </div>
        ))}
      </div>
      
      <div className="border-t border-slate-100 p-5">
        <Link href="/onboarding" className="flex items-center text-sm font-medium text-slate-500 hover:text-slate-900">
          Need help? <span className="ml-1 text-blue-600">Open onboarding guide</span> <ArrowRight className="ml-1 size-4 text-blue-600" />
        </Link>
      </div>
    </div>
  );
}
