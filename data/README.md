# Database Dumps

This directory contains database dump files that can be committed to git.

## Exporting Database

To export your current database to a SQL file:

```bash
./scripts/export_db.sh
```

This will create `database_dump.sql` in this directory.

## Importing Database

To import a database dump:

```bash
./scripts/import_db.sh
```

Or specify a custom file:

```bash
./scripts/import_db.sh path/to/dump.sql
```

## Notes

- Database dumps can be large (especially with 1000+ movies)
- Consider using Git LFS for large files if the dump exceeds 50MB
- The dump includes both schema and data
- Make sure Docker container is running before importing/exporting

