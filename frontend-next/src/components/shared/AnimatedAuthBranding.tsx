"use client";

import { motion } from "framer-motion";
import { AnswerlyLogo } from "@/components/shared/AnswerlyLogo";

export function AnimatedAuthBranding() {
  return (
    <div className="mx-auto max-w-lg">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
        className="mb-8"
      >
        <AnswerlyLogo />
      </motion.div>
      
      <motion.h1 
        initial={{ opacity: 0, x: -30 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.8, delay: 0.2, ease: "easeOut" }}
        className="mb-4 text-4xl font-bold text-[#162758]"
      >
        AI that answers.
        <br />
        People who succeed.
      </motion.h1>
      
      <motion.div 
        initial={{ scaleX: 0 }}
        animate={{ scaleX: 1 }}
        transition={{ duration: 0.8, delay: 0.6, ease: "easeOut" }}
        className="mt-8 h-1 w-12 origin-left bg-blue-600" 
      />
      
      <motion.p 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 1, delay: 0.8 }}
        className="mt-6 text-lg text-slate-600"
      >
        Answerly helps teams unlock knowledge, automate answers, and get more done—faster and smarter.
      </motion.p>
    </div>
  );
}
