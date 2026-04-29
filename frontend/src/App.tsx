import { Navigate, Route, Routes } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { useAuth } from './contexts/AuthContext';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { Alerts } from './pages/soc/Alerts';
import { Incidents } from './pages/soc/Incidents';
import { Cases } from './pages/soc/Cases';
import { SIEM } from './pages/soc/SIEM';
import { Assets } from './pages/noc/Assets';
import { Network } from './pages/noc/Network';
import { AttackPlans } from './pages/redteam/AttackPlans';
import { RedTeamExecutions } from './pages/redteam/Executions';
import { Recon } from './pages/redteam/Recon';
import { Payloads } from './pages/redteam/Payloads';
import { DetectionRules } from './pages/blueteam/DetectionRules';
import { ThreatHunting } from './pages/blueteam/ThreatHunting';
import { EDR } from './pages/blueteam/EDR';
import { FIM } from './pages/blueteam/FIM';
import { Exercises } from './pages/purpleteam/Exercises';
import { Coverage } from './pages/purpleteam/Coverage';
import { IOCs } from './pages/intel/IOCs';
import { ThreatActors } from './pages/intel/ThreatActors';
import { Campaigns } from './pages/intel/Campaigns';
import { Feeds } from './pages/intel/Feeds';
import { Vulnerabilities } from './pages/vulns/Vulnerabilities';
import { Findings } from './pages/vulns/Findings';
import { Scans } from './pages/vulns/Scans';
import { Playbooks } from './pages/ir/Playbooks';
import { IRExecutions } from './pages/ir/IRExecutions';
import { Frameworks } from './pages/compliance/Frameworks';
import { Reports } from './pages/reports/Reports';
import { UsersPage } from './pages/settings/Users';
import { AuditLog } from './pages/settings/AuditLog';
import { SystemSettings } from './pages/settings/System';
import { Engine } from './pages/settings/Engine';

function App() {
  const { isAuthenticated, loading } = useAuth();

  if (loading) return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center">
      <div className="text-gray-600 text-sm">Loading…</div>
    </div>
  );

  if (!isAuthenticated) return (
    <>
      <Login />
      <Toaster position="top-right" toastOptions={{ style: { background: '#1f2937', color: '#f3f4f6', border: '1px solid #374151' } }} />
    </>
  );

  return (
    <>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/soc/alerts" element={<Alerts />} />
        <Route path="/soc/incidents" element={<Incidents />} />
        <Route path="/soc/cases" element={<Cases />} />
        <Route path="/soc/siem" element={<SIEM />} />
        <Route path="/noc/assets" element={<Assets />} />
        <Route path="/noc/network" element={<Network />} />
        <Route path="/redteam/plans" element={<AttackPlans />} />
        <Route path="/redteam/executions" element={<RedTeamExecutions />} />
        <Route path="/redteam/recon" element={<Recon />} />
        <Route path="/redteam/payloads" element={<Payloads />} />
        <Route path="/blueteam/rules" element={<DetectionRules />} />
        <Route path="/blueteam/hunting" element={<ThreatHunting />} />
        <Route path="/blueteam/edr" element={<EDR />} />
        <Route path="/blueteam/fim" element={<FIM />} />
        <Route path="/purpleteam/exercises" element={<Exercises />} />
        <Route path="/purpleteam/coverage" element={<Coverage />} />
        <Route path="/intel/iocs" element={<IOCs />} />
        <Route path="/intel/actors" element={<ThreatActors />} />
        <Route path="/intel/campaigns" element={<Campaigns />} />
        <Route path="/intel/feeds" element={<Feeds />} />
        <Route path="/vulns/list" element={<Vulnerabilities />} />
        <Route path="/vulns/findings" element={<Findings />} />
        <Route path="/vulns/scans" element={<Scans />} />
        <Route path="/ir/playbooks" element={<Playbooks />} />
        <Route path="/ir/executions" element={<IRExecutions />} />
        <Route path="/compliance/frameworks" element={<Frameworks />} />
        <Route path="/reports" element={<Reports />} />
        <Route path="/settings/users" element={<UsersPage />} />
        <Route path="/settings/audit" element={<AuditLog />} />
        <Route path="/settings/system" element={<SystemSettings />} />
        <Route path="/settings/engine" element={<Engine />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <Toaster position="top-right" toastOptions={{ style: { background: '#1f2937', color: '#f3f4f6', border: '1px solid #374151' } }} />
    </>
  );
}

export default App;
