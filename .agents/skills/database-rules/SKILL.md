---
name: database-rules
description: Enforces strict type safety, SQLite WAL mode, and explicit transactional blocks for all database scripts.
---

# Database Rules

When working on the Raj-CXR Silicosis Screening Platform database, you must adhere to the following rules:

1. **Strict Type Safety**: Use `STRICT` mode for all SQLite tables to enforce data types.
2. **Crash Resiliency**: Always enable Write-Ahead Logging (WAL) and foreign keys using PRAGMAs:
   ```sql
   PRAGMA foreign_keys = ON;
   PRAGMA journal_mode = WAL;
   ```
3. **Transactional Blocks**: All database write operations must be wrapped in explicit transactional blocks (`try...except` in Python with `commit()` on success and `rollback()` on failure).
4. **Primary Keys**: Ensure tables use explicit and appropriate primary keys (e.g., standard formats like `jan_aadhaar_no` or UUIDs).
