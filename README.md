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

## Setup tests

```sh
nix build .#postgresql-devel
podman load < result
podman run -p 54320:5432 --name database -dt postgresql:latest
nix build .#redis-devel
podman load < result
podman run -p 63790:63790 --name cache -dt redis:latest
nix develop
pdm install --dev
eval $(pdm venv activate)
pytest
```

## Side notes 

```
/var
  /lib
    /materia    <-- data directory
      /repository   <-- repository directory 
        /rick   <-- user name
          /default  <--| default repository name 
          ...          | possible features: external cloud drives?
            /first  <-- first level directories counts as root because no parent
              /nested
                /hello.txt
```

# License

**materia** is licensed under the [MIT License](LICENSE).
