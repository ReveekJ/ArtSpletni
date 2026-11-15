from app.db.models import ContentBlock, Point
from app.domain.i18n.schemas import localized_out
from app.domain.points.schemas import AdminBlockOut, AdminPointOut, AdminPointSummary


def admin_block_out(block: ContentBlock) -> AdminBlockOut:
    return AdminBlockOut(
        id=block.id,
        kind=block.kind,
        text=localized_out(block.text),
        caption=localized_out(block.caption),
        transcript=localized_out(block.transcript),
        asset_id=block.asset_id,
        media_variants={variant.language: variant.asset_id for variant in block.media_variants},
    )


def admin_point_out(point: Point) -> AdminPointOut:
    return AdminPointOut(
        id=point.id,
        kind=point.kind,
        title=localized_out(point.title),
        latitude=point.latitude,
        longitude=point.longitude,
        address=localized_out(point.address),
        note=localized_out(point.note),
        cover_asset_id=point.cover_asset_id,
        partner_id=point.partner_id,
        is_published=point.is_published,
        blocks=[admin_block_out(block) for block in point.blocks],
        created_at=point.created_at,
        updated_at=point.updated_at,
    )


def admin_point_summary(point: Point) -> AdminPointSummary:
    return AdminPointSummary(
        id=point.id,
        kind=point.kind,
        title=localized_out(point.title),
        latitude=point.latitude,
        longitude=point.longitude,
        is_published=point.is_published,
        updated_at=point.updated_at,
    )
