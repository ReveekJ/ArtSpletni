import { Navigate, Outlet } from "react-router-dom";

import { Loader } from "@/components/Loader";
import { useCurrentUser, useSession } from "@/features/auth/api";
import { AdminSidebar } from "@/features/admin/AdminSidebar";

export default function AdminLayout() {
  const session = useSession();
  const user = useCurrentUser();
  if (session.isPending) return <Loader />;
  if (user?.role !== "admin") return <Navigate to="/login?next=/admin" replace />;
  return (
    <div className="flex min-h-dvh flex-col lg:flex-row">
      <AdminSidebar />
      <main className="box-border flex min-w-0 flex-1 flex-col gap-6 px-[clamp(20px,3vw,40px)] pt-7 pb-10">
        <Outlet />
      </main>
    </div>
  );
}
