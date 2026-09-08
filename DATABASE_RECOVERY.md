# AspireOS Database Recovery Guide

This document outlines the backup and restore procedures for the AspireOS MVP, which utilizes SQLite (`data/app.db`) as its primary data store.

## 1. Backing Up the Database

Since SQLite is a file-based database, backing it up is a straightforward file copy operation. However, to ensure consistency and prevent data corruption, you must create a backup safely while the application is running, or stop the application.

### Safest Approach (Application Stopped)
1. Stop the `uvicorn` server.
2. Copy the database file:
   ```bash
   cp data/app.db data/app.db.backup.$(date +%F)
   ```
3. Restart the server.

### Hot Backup (Application Running)
If stopping the application is not feasible, use the SQLite Online Backup API or the `sqlite3` CLI tool to create a consistent snapshot without halting writes:
```bash
sqlite3 data/app.db ".backup 'data/app.db.backup.$(date +%F)'"
```

## 2. Restoring the Database

**WARNING**: Restoring the database will overwrite all current data with the state at the time of the backup.

To restore a backup:
1. **Stop the application** (`uvicorn` server) to prevent any writes during the restore process.
2. Move the corrupted or current database to a safe location (do not just delete it):
   ```bash
   mv data/app.db data/app.db.corrupted
   ```
3. Copy the backup file to the active location:
   ```bash
   cp data/app.db.backup.YYYY-MM-DD data/app.db
   ```
4. **Restart the application**.

## 3. Encryption Keys

**CRITICAL**: The database contains encrypted fields (e.g., private diagnostic notes). These fields are encrypted using the Fernet symmetric encryption key. 
If you restore an old database, you **MUST** have the exact same `FERNET_KEY` (either in the `.env` variable or the `.fernet_key` file) that was used to encrypt the data at that time. Without this key, the encrypted fields will be permanently unreadable. Back up your `.fernet_key` alongside your database backups!
