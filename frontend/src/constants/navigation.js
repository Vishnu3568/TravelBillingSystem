import { 
  Home, Building2, Truck, Users, BarChart2, 
  Database, ClipboardList, Settings, UploadCloud,
  PlusCircle, FileText, Car 
} from 'lucide-react';

export const routes = [
  { to: '/', icon: Home, label: 'Home' },
  { to: '/bill-history', icon: FileText, label: 'Bills' },
  { to: '/companies', icon: Building2, label: 'Companies', roles: ['OWNER', 'MANAGER'] },
  { to: '/vehicles', icon: Car, label: 'Vehicles', roles: ['OWNER', 'MANAGER'] },
  { to: '/users', icon: Users, label: 'Users', roles: ['OWNER'] },
  { to: '/import-bills', icon: UploadCloud, label: 'Bulk Upload', roles: ['OWNER'] },
  { to: '/reports', icon: BarChart2, label: 'Reports', roles: ['OWNER', 'MANAGER'] },
  { to: '/backup', icon: Database, label: 'Backup', roles: ['OWNER'] },
  { to: '/settings', icon: Settings, label: 'Settings' },
];
