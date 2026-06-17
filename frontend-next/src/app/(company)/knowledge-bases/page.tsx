"use client";

import { useQuery } from "@tanstack/react-query";
import { Search, Filter, BookOpen, Bot, LayoutGrid, List, Info, RefreshCw, TrendingUp, Link as LinkIcon, Plus } from "lucide-react";

import { listProjects, normalizeProjectListResponse } from "@/lib/api/projects";
import { listBotIntegrations } from "@/lib/api/botIntegrations";

import { KnowledgeBaseFormDialog } from "@/components/knowledge-bases/KnowledgeBaseFormDialog";
import { KnowledgeBaseTable } from "@/components/knowledge-bases/KnowledgeBaseTable";
import { EmptyState } from "@/components/shared/EmptyState";
import { ErrorState } from "@/components/shared/ErrorState";
import { LoadingState } from "@/components/shared/LoadingState";
import { Button } from "@/components/ui/button";

export default function KnowledgeBasesPage() {
  const query = useQuery({
    queryKey: ["projects"],
    queryFn: listProjects,
    select: normalizeProjectListResponse,
  });

  const botsQuery = useQuery({
    queryKey: ["botIntegrations"],
    queryFn: listBotIntegrations,
  });

  if (query.isLoading || botsQuery.isLoading) {
    return <LoadingState label="Loading knowledge bases..." />;
  }

  if (query.isError || botsQuery.isError) {
    return <ErrorState description="Failed to load knowledge bases." onRetry={() => query.refetch()} />;
  }

  const projects = query.data || [];
  const bots = botsQuery.data || [];

  return (
    <div className="space-y-8 pb-10">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900 tracking-tight">Knowledge Bases</h1>
          <p className="text-sm text-slate-500 mt-1">
            Organize and manage your company's knowledge repositories.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <KnowledgeBaseFormDialog trigger={
            <Button className="h-10 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm px-4">
              <Plus className="mr-2 size-4" />
              New Knowledge Base
            </Button>
          }/>
          <div className="relative hidden sm:block">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-slate-400" />
            <input 
              type="text" 
              placeholder="Search knowledge bases..." 
              className="h-10 w-64 rounded-xl border border-slate-200 pl-9 pr-4 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 transition-shadow"
            />
          </div>
          <Button variant="outline" className="h-10 rounded-xl px-3 border-slate-200 text-slate-600">
            <Filter className="size-4 mr-2" />
            Filters
          </Button>
        </div>
      </div>

      <div className="relative overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm p-8 sm:p-10">
        <div className="absolute top-0 right-0 w-1/2 h-full bg-gradient-to-l from-indigo-50/50 to-transparent pointer-events-none" />
        <div className="relative z-10 flex flex-col sm:flex-row sm:items-center gap-8">
          <div className="relative size-32 shrink-0">
            <div className="absolute inset-0 rounded-full bg-indigo-100/50 blur-xl" />
            <div className="relative size-full rounded-full border-4 border-white bg-indigo-50 flex items-center justify-center shadow-inner">
              <BookOpen className="size-10 text-indigo-500" />
            </div>
            <div className="absolute -top-2 -right-2 size-10 rounded-full bg-white shadow-md flex items-center justify-center border border-slate-100">
              <MessageSquareText className="size-5 text-emerald-500" />
            </div>
            <div className="absolute -bottom-2 -left-2 size-10 rounded-full bg-white shadow-md flex items-center justify-center border border-slate-100">
              <Bot className="size-5 text-blue-500" />
            </div>
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-900">Build your company knowledge hub</h2>
            <p className="mt-2 text-slate-600 max-w-xl leading-relaxed">
              Knowledge Bases store your documents and content so your bots can answer questions accurately and consistently.
            </p>
            <div className="mt-5 flex items-center gap-3">
              <KnowledgeBaseFormDialog trigger={
                <Button className="rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm">
                  <Plus className="mr-2 size-4" />
                  Create your first Knowledge Base
                </Button>
              }/>
              <Button variant="outline" className="rounded-xl border-slate-200">
                Learn more
                <ExternalLink className="ml-2 size-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>

      {projects.length === 0 ? (
        <EmptyState
          title="No knowledge bases yet"
          description="Create the first one to start uploading documents and testing retrieval."
        />
      ) : (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center rounded-lg border border-slate-200 bg-white p-1">
              <button className="flex items-center gap-2 rounded-md bg-slate-100 px-3 py-1.5 text-sm font-medium text-slate-900 shadow-sm">
                <List className="size-4" />
                Table view
              </button>
              <button className="flex items-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium text-slate-500 hover:text-slate-900 transition-colors">
                <LayoutGrid className="size-4" />
                Card view
              </button>
            </div>
            <div className="flex items-center gap-3 text-sm text-slate-500">
              <span>{projects.length} knowledge bases</span>
              <button className="p-1.5 hover:bg-slate-100 rounded-md transition-colors">
                <RefreshCw className="size-4" />
              </button>
            </div>
          </div>

          <KnowledgeBaseTable projects={projects} bots={bots} />
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-8">
        <div className="rounded-2xl border border-slate-200 bg-indigo-50/50 p-5 flex items-start gap-3">
          <Info className="size-5 text-indigo-500 shrink-0 mt-0.5" />
          <div>
            <h4 className="font-semibold text-slate-900 text-sm">Tips</h4>
            <p className="text-xs text-slate-500 mt-1">Best practices for knowledge bases.</p>
          </div>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-5 flex items-start gap-4 shadow-sm">
          <div className="rounded-xl bg-emerald-50 p-2.5 text-emerald-600 ring-1 ring-emerald-100 shrink-0">
            <RefreshCw className="size-4" />
          </div>
          <div>
            <h4 className="font-semibold text-slate-900 text-sm">Keep your content fresh</h4>
            <p className="text-xs text-slate-500 mt-1">Regularly update documents for better accuracy.</p>
          </div>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-5 flex items-start gap-4 shadow-sm">
          <div className="rounded-xl bg-blue-50 p-2.5 text-blue-600 ring-1 ring-blue-100 shrink-0">
            <TrendingUp className="size-4" />
          </div>
          <div>
            <h4 className="font-semibold text-slate-900 text-sm">Improve readiness</h4>
            <p className="text-xs text-slate-500 mt-1">Higher readiness means better bot performance.</p>
          </div>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-5 flex items-start gap-4 shadow-sm relative group">
          <div className="rounded-xl bg-indigo-50 p-2.5 text-indigo-600 ring-1 ring-indigo-100 shrink-0">
            <Bot className="size-4" />
          </div>
          <div>
            <h4 className="font-semibold text-slate-900 text-sm">Connect to bots</h4>
            <p className="text-xs text-slate-500 mt-1">Link knowledge bases to bots to enable smart responses.</p>
          </div>
          <button className="absolute top-3 right-3 text-slate-300 hover:text-slate-500 opacity-0 group-hover:opacity-100 transition-opacity">
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M9 3L3 9M3 3L9 9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}

// Ensure icons used in render are imported
import { MessageSquareText, ExternalLink } from "lucide-react";
