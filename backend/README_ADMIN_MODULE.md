# Heritage Portal Backend – Admin Module

This backend is aligned to the team schema supplied by Member 4:
`users`, `heritage_sites`, `contributions`, and `feedback`.

## Local setup

1. Create/activate your Python virtual environment.
2. Install dependencies: `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and enter your own local MySQL credentials and long random secret keys.
4. Set `DB_NAME=heritage_db` (the database name confirmed by the team).
5. Use the team's existing Flask-Migrate/Alembic migration history. Do not run `db.create_all()` against the shared/team database.
6. Start the server with `python run.py`.

## Admin authentication

Log in using `POST /api/auth/login`. Send the returned access token as:
`Authorization: Bearer <access_token>`.
The token must contain `role: admin`; the token identity is used for `admin_id` and review audit fields.

## Admin endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/admin/dashboard` | Dashboard counts |
| POST | `/api/admin/heritage` | Add a heritage site |
| GET | `/api/admin/heritage` | List all sites |
| GET | `/api/admin/heritage/<site_id>` | Get one site |
| PUT | `/api/admin/heritage/<site_id>` | Update a site |
| DELETE | `/api/admin/heritage/<site_id>` | Delete a site; contribution references are set to NULL first |
| GET | `/api/admin/contributions` | List contributions; optional `?status=pending` |
| PUT | `/api/admin/contributions/<id>/approve` | Approve and publish a contribution |
| PUT | `/api/admin/contributions/<id>/reject` | Reject a contribution |
| GET | `/api/admin/feedback` | List feedback |
| DELETE | `/api/admin/feedback/<id>` | Delete feedback |

### Add heritage site JSON

```json
{
  "name": "Example Fort",
  "description": "A historic fort.",
  "location": "Example City",
  "state": "Maharashtra",
  "category": "Fort",
  "historical_significance": "Historical details",
  "latitude": 17.0,
  "longitude": 74.0,
  "image_url": "https://example.com/fort.jpg"
}
```

### Approve contribution JSON

The finalized `contributions` table stores only `title` and `description` as the proposed site details. Therefore the admin must provide the missing site location and state when approving:

```json
{
  "location": "Example City",
  "state": "Maharashtra",
  "category": "Fort",
  "historical_significance": "Historical details",
  "latitude": 17.0,
  "longitude": 74.0,
  "image_url": "https://example.com/fort.jpg",
  "remark": "Verified and approved"
}
```

### Reject contribution JSON

```json
{
  "remark": "Please provide a reliable source for this information."
}
```

## Important integration note

The public contribution endpoint now accepts `title` and `description`, matching Member 4's schema. The public feedback endpoint accepts `message` and optional `rating`, plus optional `name` and `email`. Public heritage listing uses `status="active"`, matching Member 4's model default.

The source files were syntax-checked with Python compileall. Live database and Postman tests still need to be run against the team's `heritage_db` database and migration version.
