import { 
  Home, Building2, Truck, Users, BarChart2, 
  Database, ClipboardList, Settings, UploadCloud,
  PlusCircle, FileText, Car, Cpu
} from 'lucide-react';

export const routes = [
  { to: '/', icon: Home, label: 'Home' },
  { to: '/bill-history', icon: FileText, label: 'Bills' },
  { to: '/companies', icon: Building2, label: 'Companies', roles: ['OWNER', 'MANAGER'] },
  { to: '/vehicles', icon: Car, label: 'Vehicles', roles: ['OWNER', 'MANAGER'] },
  { to: '/owner-dashboard/import-bills', icon: UploadCloud, label: 'Bulk Upload', roles: ['OWNER'] },
  { to: '/amip-control-center', icon: Cpu, label: 'AMIP Control', roles: ['OWNER', 'MANAGER'] },
  { to: '/users', icon: Users, label: 'Users', roles: ['OWNER'] },
  { to: '/reports', icon: BarChart2, label: 'Reports', roles: ['OWNER', 'MANAGER'] },
  { to: '/settings', icon: Settings, label: 'Settings' },
];
