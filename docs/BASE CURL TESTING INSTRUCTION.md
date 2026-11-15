# cURL testing

Run the API (`server/`) and point `BASE_URL` at it. Sessions are cookies, so keep one cookie jar per actor.

```bash
BASE_URL=http://localhost:8000
ADMIN=/tmp/spletni-admin.txt
PLAYER=/tmp/spletni-player.txt
```

Create an administrator once (local database only):

```bash
cd server && LITESTAR_APP=app.asgi:create_app uv run litestar create-admin --email admin@spletni.local
```

## Admin session

```bash
curl -s -c $ADMIN -H 'Content-Type: application/json' \
  -d '{"email":"admin@spletni.local","password":"<password>"}' $BASE_URL/api/auth/login
```

## Point, NFC tag and scan

```bash
POINT_ID=$(curl -s -b $ADMIN -H 'Content-Type: application/json' \
  -d '{"kind":"gossip","title":{"ru":"Дом"},"latitude":55.75,"longitude":37.61,"isPublished":true,
       "blocks":[{"kind":"text","text":{"ru":"Говорят..."}}]}' \
  $BASE_URL/api/admin/points | python3 -c 'import sys,json;print(json.load(sys.stdin)["id"])')

TAG_URL=$(curl -s -b $ADMIN -H 'Content-Type: application/json' -d '{"label":"main"}' \
  $BASE_URL/api/admin/points/$POINT_ID/tags | python3 -c 'import sys,json;print(json.load(sys.stdin)["url"])')
TOKEN=${TAG_URL##*/}

curl -s -c $PLAYER -b $PLAYER -H 'Content-Type: application/json' -d "{\"token\":\"$TOKEN\"}" $BASE_URL/api/scans
curl -s -b $PLAYER $BASE_URL/api/points/$POINT_ID
curl -s -b $PLAYER $BASE_URL/api/me/collection
```

The tag URL is shown only once, at issue time. A lost URL means issuing a new tag
(`POST /api/admin/points/{id}/tags`) and revoking the old one (`POST /api/admin/tags/{id}/revoke`).

## Route

```bash
ROUTE_ID=$(curl -s -b $ADMIN -H 'Content-Type: application/json' \
  -d '{"slug":"center","title":{"ru":"Центр"},"orderingMode":"sequential","mapVisibility":"progressive"}' \
  $BASE_URL/api/admin/routes | python3 -c 'import sys,json;print(json.load(sys.stdin)["id"])')
curl -s -b $ADMIN -H 'Content-Type: application/json' -d "{\"pointId\":\"$POINT_ID\",\"isStart\":true}" \
  $BASE_URL/api/admin/routes/$ROUTE_ID/stops
curl -s -b $ADMIN -X POST $BASE_URL/api/admin/routes/$ROUTE_ID/publish
curl -s -b $PLAYER $BASE_URL/api/routes/center
```

## Useful checks

| Check | Request |
| --- | --- |
| Current session | `GET /api/auth/session` |
| My runs / offers / achievements | `GET /api/runs`, `GET /api/me/offers`, `GET /api/me/achievements` |
| Partner redemption | `POST /api/partner/{partnerId}/redemptions` with `{"code": "..."}` |
| Admin overview | `GET /api/admin/analytics/overview?days=7` |
| OpenAPI | `GET /schema` (Scalar UI), `GET /schema/openapi.json` |

Errors always return `{"detail": "...", "code": "..."}`; assert on `code`.
