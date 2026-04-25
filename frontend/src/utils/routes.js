export function dashboardPathForRole(role) {
  switch (role) {
    case "OWNER":
      return "/owner-dashboard";
    case "MANAGER":
      return "/manager-dashboard";
    case "EMPLOYEE":
      return "/employee-dashboard";
    default:
      return "/login";
  }
}
