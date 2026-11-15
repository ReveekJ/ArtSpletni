import { useTranslation } from "react-i18next";
import { Link, useParams } from "react-router-dom";

import { ErrorText } from "@/components/ErrorText";
import { Loader } from "@/components/Loader";
import { Button } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";
import { useAdminPartners } from "@/features/admin/api";
import { PartnerMembers } from "@/features/admin/partners/PartnerMembers";
import { PartnerOffers } from "@/features/admin/partners/PartnerOffers";
import { PartnerSettings } from "@/features/admin/partners/PartnerSettings";
import { PageHeader } from "@/features/admin/ui/PageHeader";

export { PartnersListPage } from "@/features/admin/partners/PartnersListPage";

export default function PartnerDetailPage() {
  const { partnerId = "" } = useParams();
  const { t } = useTranslation();
  const partners = useAdminPartners();
  const partner = partners.data?.find((item) => item.id === partnerId);
  if (partners.isPending) return <Loader />;
  if (!partner) return <ErrorText error={partners.error} code="not_found" />;
  return (
    <>
      <div className="flex items-center gap-3">
        <Button asChild variant="outline" size="icon">
          <Link to="/admin/partners" aria-label={t("app.admin.partners")}>
            <Icon name="arrow-left" />
          </Link>
        </Button>
        <PageHeader eyebrow={t("app.admin.partner")} title={partner.name} />
      </div>
      <div className="grid items-start gap-6 2xl:grid-cols-[minmax(0,1fr)_380px]">
        <PartnerOffers partnerId={partner.id} />
        <div className="flex flex-col gap-6">
          <PartnerSettings partner={partner} />
          <PartnerMembers partnerId={partner.id} />
        </div>
      </div>
    </>
  );
}
