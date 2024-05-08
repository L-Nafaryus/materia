# materia

Materia is a file server.

## Database migrations
```bash 
# Initialize
alembic init -t async src/db/migrations 

# Autogenerate new migration 
alembic revision --autogenerate -m "Initial migration"

# Apply the migration
alembic upgrade head

# Rollback the migration 
alembic downgrade head
```
# License

**materia** is licensed under the [MIT License](LICENSE).
