import React from 'react'
import { FileText, CheckCircle, XCircle, Cloud } from 'lucide-react'

const StatCard = ({ icon: Icon, number, label, bgGradient }) => {
  return (
    <div className={`${bgGradient} rounded-2xl p-6 text-white text-center hover:shadow-lg transition-all`}>
      <div className="text-5xl font-bold font-poppins mb-2">{number}</div>
      <div className="flex items-center justify-center gap-2 text-sm font-semibold">
        <Icon className="w-4 h-4" />
        <span>{label}</span>
      </div>
    </div>
  )
}

export const StatsSection = ({ stats }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
      <StatCard
        icon={FileText}
        number={stats.totalFiles}
        label="Selected Files"
        bgGradient="bg-gradient-to-br from-indigo-500 to-purple-600 dark:from-indigo-600 dark:to-purple-700"
      />
      <StatCard
        icon={CheckCircle}
        number={stats.validFiles}
        label="Valid Files"
        bgGradient="bg-gradient-to-br from-green-500 to-emerald-600 dark:from-green-600 dark:to-emerald-700"
      />
      <StatCard
        icon={XCircle}
        number={stats.invalidFiles}
        label="Invalid Files"
        bgGradient="bg-gradient-to-br from-red-500 to-rose-600 dark:from-red-600 dark:to-rose-700"
      />
      <StatCard
        icon={Cloud}
        number={stats.uploadedFiles}
        label="Total Uploaded"
        bgGradient="bg-gradient-to-br from-blue-500 to-cyan-600 dark:from-blue-600 dark:to-cyan-700"
      />
    </div>
  )
}
