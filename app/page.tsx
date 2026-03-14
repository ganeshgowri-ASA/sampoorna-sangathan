const modules = [
  { name: 'JanaSeva (HRMS)', icon: '👥', desc: 'Human Resource Management', status: 'Phase 1' },
  { name: 'SambandhaPath (CRM)', icon: '🤝', desc: 'Customer Relationship Management', status: 'Phase 1' },
  { name: 'KoshaPrabandhan (Finance)', icon: '💰', desc: 'Financial Management & Accounting', status: 'Phase 2' },
  { name: 'BhandarGriha (Inventory)', icon: '📦', desc: 'Inventory & Warehouse Management', status: 'Phase 2' },
  { name: 'PariyojanaChakra (Projects)', icon: '📋', desc: 'Project Management & Tasks', status: 'Phase 1' },
  { name: 'LekhaPeethika (Office)', icon: '📝', desc: 'Office Suite & Documents', status: 'Phase 3' },
]

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="max-w-7xl mx-auto px-4 py-16">
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold text-white mb-4">
            SampoornaSangathan
          </h1>
          <p className="text-xl text-amber-400 mb-2">सम्पूर्णसंगठन</p>
          <p className="text-lg text-slate-300">
            Unified Organisation OS | AI-Native Enterprise Platform
          </p>
          <div className="mt-4 inline-flex items-center gap-2 bg-green-500/10 border border-green-500/30 rounded-full px-4 py-2">
            <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
            <span className="text-green-400 text-sm">System Online</span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-16">
          {modules.map((mod) => (
            <div key={mod.name} className="bg-slate-800/50 border border-slate-700 rounded-xl p-6 hover:border-amber-500/50 transition-all">
              <div className="text-4xl mb-3">{mod.icon}</div>
              <h3 className="text-lg font-semibold text-white">{mod.name}</h3>
              <p className="text-slate-400 text-sm mt-1">{mod.desc}</p>
              <span className="inline-block mt-3 text-xs bg-amber-500/20 text-amber-400 px-2 py-1 rounded">{mod.status}</span>
            </div>
          ))}
        </div>

        <div className="text-center text-slate-500 text-sm">
          <p>Built with Next.js + Vercel + Railway PostgreSQL + Prisma</p>
          <p className="mt-1">22 Modules Planned | Phase 1 Active</p>
        </div>
      </div>
    </main>
  )
}
