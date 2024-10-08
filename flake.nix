{
  description = "Materia";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    dream2nix = {
      url = "github:nix-community/dream2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    bonfire.url = "github:L-Nafaryus/bonfire";
    nix-std.url = "github:chessai/nix-std";
  };

  outputs = {
    self,
    nixpkgs,
    dream2nix,
    bonfire,
    nix-std,
    ...
  }: let
    system = "x86_64-linux";
    pkgs = import nixpkgs {inherit system;};
    bonLib = bonfire.lib;

    dreamBuildPackage = {
      module,
      meta ? {},
      extraModules ? [],
      extraArgs ? {},
    }:
      (
        nixpkgs.lib.evalModules {
          modules = [module] ++ extraModules;
          specialArgs =
            {
              inherit dream2nix;
              packageSets.nixpkgs = pkgs;
            }
            // extraArgs;
        }
      )
      .config
      .public
      // {inherit meta;};
  in {
    packages.x86_64-linux = {
      materia-frontend-vue = dreamBuildPackage {
        module = {
          lib,
          config,
          dream2nix,
          ...
        }: {
          name = "materia-frontend-vue";
          version = "0.1.1";

          imports = [
            dream2nix.modules.dream2nix.WIP-nodejs-builder-v3
          ];

          mkDerivation = {
            src = ./packages/frontend;
          };

          deps = {nixpkgs, ...}: {
            inherit
              (nixpkgs)
              fetchFromGitHub
              stdenv
              ;
          };

          WIP-nodejs-builder-v3 = {
            packageLockFile = "${config.mkDerivation.src}/package-lock.json";
          };
        };
        meta = with nixpkgs.lib; {
          description = "Materia is a simple and fast cloud storage (vue)";
          homepage = "https://materia.elnafo.ru";
          license = licenses.mit;
          maintainers = with bonLib.maintainers; [L-Nafaryus];
          broken = false;
        };
      };

      materia-frontend = dreamBuildPackage {
        extraArgs = {
          inherit (self.packages.x86_64-linux) materia-frontend-vue;
        };
        module = {
          config,
          lib,
          dream2nix,
          materia-frontend-vue,
          ...
        }: {
          imports = [dream2nix.modules.dream2nix.WIP-python-pdm];

          pdm.lockfile = ./pdm.lock;
          pdm.pyproject = ./packages/frontend/pyproject.toml;

          deps = _: {
            python = pkgs.python312;
          };

          mkDerivation = {
            src = ./packages/frontend;
            buildInputs = [
              pkgs.python312.pkgs.pdm-backend
            ];
            configurePhase = ''
              mkdir -p target/materia_frontend
              cp -rv ${materia-frontend-vue}/dist/* ./target/materia_frontend/
              cp -rv templates ./target/materia_frontend/
              touch target/materia_frontend/__init__.py
            '';
          };
        };
        meta = with nixpkgs.lib; {
          description = "Materia is a simple and fast cloud storage (frontend)";
          homepage = "https://materia.elnafo.ru";
          license = licenses.mit;
          maintainers = with bonLib.maintainers; [L-Nafaryus];
          broken = false;
        };
      };

      materia-server = pkgs.callPackage ({
        withFrontend ? true,
        withDocs ? true,
        ...
      }:
        dreamBuildPackage {
          extraArgs = {
            inherit (self.packages.x86_64-linux) materia-frontend materia-docs;
          };
          module = {
            config,
            lib,
            dream2nix,
            materia-frontend,
            materia-docs,
            ...
          }: {
            imports = [dream2nix.modules.dream2nix.WIP-python-pdm];

            pdm.lockfile = ./pdm.lock;
            pdm.pyproject = ./packages/server/pyproject.toml;

            deps = _: {
              python = pkgs.python312;
            };

            mkDerivation = {
              src = ./packages/server;
              buildInputs = [
                pkgs.python312.pkgs.pdm-backend
              ];
              nativeBuildInputs = [
                pkgs.python312.pkgs.wrapPython
              ];
              propagatedBuildInputs =
                lib.optionals withFrontend [
                  materia-frontend
                ]
                ++ lib.optionals withDocs [materia-docs];
            };
          };
          meta = with nixpkgs.lib; {
            description = "Materia is a simple and fast cloud storage";
            homepage = "https://materia.elnafo.ru";
            license = licenses.mit;
            maintainers = with bonLib.maintainers; [L-Nafaryus];
            broken = false;
            mainProgram = "materia";
          };
        }) {};

      materia-docs = dreamBuildPackage {
        extraArgs = {
          materia-server = self.packages.x86_64-linux.materia-server.override {
            withFrontend = false;
            withDocs = false;
          };
        };
        module = {
          config,
          lib,
          dream2nix,
          materia-server,
          ...
        }: {
          imports = [dream2nix.modules.dream2nix.WIP-python-pdm];

          pdm.lockfile = ./pdm.lock;
          pdm.pyproject = ./packages/docs/pyproject.toml;

          deps = _: {
            python = pkgs.python312;
          };

          mkDerivation = {
            src = ./packages/docs;
            buildInputs = [
              pkgs.python312.pkgs.pdm-backend
            ];
            nativeBuildInputs = [pkgs.mkdocs materia-server];
            configurePhase = ''
              mkdir -p target/materia_docs
              mkdocs build
              touch target/materia_docs/__init__.py
            '';
          };
        };
        meta = with nixpkgs.lib; {
          description = "Materia is a simple and fast cloud storage (docs)";
          homepage = "https://materia.elnafo.ru";
          license = licenses.mit;
          maintainers = with bonLib.maintainers; [L-Nafaryus];
          broken = false;
        };
      };

      postgresql-devel = bonfire.packages.x86_64-linux.postgresql;

      redis-devel = bonfire.packages.x86_64-linux.redis;

      materia-devel = let
        user = "materia";
        dataDir = "/var/lib/materia";
        entryPoint = pkgs.writeTextDir "entrypoint.sh" ''
          materia start
        '';
      in
        pkgs.dockerTools.buildImage {
          name = "materia";
          tag = "latest";

          copyToRoot = pkgs.buildEnv {
            name = "image-root";
            pathsToLink = ["/bin" "/etc" "/"];
            paths = with pkgs; [
              bash
              self.packages.x86_64-linux.materia-server
              entryPoint
            ];
          };
          runAsRoot = with pkgs; ''
            #!${runtimeShell}
            ${dockerTools.shadowSetup}
            groupadd -r ${user}
            useradd -r -g ${user} --home-dir=${dataDir} ${user}
            mkdir -p ${dataDir}
            chown -R ${user}:${user} ${dataDir}
          '';

          config = {
            Entrypoint = ["bash" "/entrypoint.sh"];
            StopSignal = "SIGINT";
            User = "${user}:${user}";
            WorkingDir = dataDir;
            ExposedPorts = {
              "54601/tcp" = {};
            };
            Env = [
              "MATERIA_APPLICATION__WORKING_DIRECTORY=${dataDir}"
            ];
          };
        };
    };

    devShells.x86_64-linux.default = pkgs.mkShell {
      buildInputs = with pkgs; [postgresql redis pdm nodejs python312];
      # greenlet requires libstdc++
      LD_LIBRARY_PATH = nixpkgs.lib.makeLibraryPath [pkgs.stdenv.cc.cc];
    };

    nixosModules = rec {
      materia = {
        config,
        lib,
        pkgs,
        ...
      }:
        with lib; let
          cfg = config.services.materia;
        in {
          options.services.materia = {
            enable = mkEnableOption "Enables the Materia service";

            package = mkOption {
              type = types.package;
              default = self.packages.x86_64-linux.materia-server;
              description = "The package to use.";
            };

            application = mkOption {
              type = types.submodule {
                options = {
                  user = mkOption {
                    type = types.str;
                  };
                  group = mkOption {
                    type = types.str;
                  };
                  mode = mkOption {
                    type = types.str;
                  };
                  working_directory = mkOption {
                    type = types.path;
                    default = "/var/lib/materia";
                  };
                };
              };
              default = {
                user = "materia";
                group = "materia";
                mode = "production";
                working_directory = "/var/lib/materia";
              };
            };

            server = mkOption {
              type = types.submodule {
                options = {
                  scheme = mkOption {
                    type = types.str;
                  };
                  address = mkOption {
                    type = types.str;
                  };
                  port = mkOption {
                    type = types.port;
                  };
                  domain = mkOption {
                    type = types.str;
                  };
                };
              };
              default = {
                scheme = "http";
                address = "127.0.0.1";
                port = 54601;
                domain = "localhost";
              };
            };

            database = mkOption {
              type = types.submodule {
                options = {
                  backend = mkOption {
                    type = types.str;
                    default = "postgresql";
                  };
                  scheme = mkOption {
                    type = types.str;
                    default = "postgresql+asyncpg";
                  };
                  address = mkOption {
                    type = types.str;
                    default = "127.0.0.1";
                  };
                  port = mkOption {
                    type = types.port;
                    default = 5432;
                  };
                  name = mkOption {
                    type = types.nullOr types.str;
                    default = "materia";
                  };
                  user = mkOption {
                    type = types.str;
                    default = "materia";
                  };
                  password = mkOption {
                    type = types.nullOr (types.oneOf [types.str types.path]);
                    default = null;
                  };
                };
              };
              default = {
                backend = "postgresql";
                scheme = "postgresql+asyncpg";
                address = "127.0.0.1";
                port = 5432;
                name = "materia";
                user = "materia";
                password = null;
              };
            };

            cache = mkOption {
              type = types.submodule {
                options = {
                  backend = mkOption {
                    type = types.str;
                    default = "redis";
                  };
                  scheme = mkOption {
                    type = types.str;
                    default = "redis";
                  };
                  address = mkOption {
                    type = types.str;
                    default = "127.0.0.1";
                  };
                  port = mkOption {
                    type = types.port;
                    default = 6379;
                  };
                  database = mkOption {
                    type = types.nullOr types.int;
                    default = 0;
                  };
                  user = mkOption {
                    type = types.str;
                    default = "materia";
                  };
                  password = mkOption {
                    type = types.nullOr (types.oneOf [types.str types.path]);
                    default = null;
                  };
                };
              };
              default = {
                backed = "redis";
                scheme = "redis";
                address = "127.0.0.1";
                port = 6379;
                database = 0;
                user = "materia";
                password = null;
              };
            };

            security = mkOption {
              type = types.submodule {
                options = {
                  secret_key = mkOption {
                    type = types.nullOr (types.oneOf [types.str types.path]);
                  };
                  password_min_length = mkOption {
                    type = types.int;
                  };
                  password_hash_algo = mkOption {
                    type = types.nullOr types.str;
                  };
                  cookie_http_only = mkOption {
                    type = types.bool;
                  };
                  cookie_access_token_name = mkOption {
                    type = types.str;
                  };
                  cookie_refresh_token_name = mkOption {
                    type = types.str;
                  };
                };
              };
              default = {
                secret_key = null;
                password_min_length = 8;
                password_hash_algo = "bcrypt";
                cookie_http_only = true;
                cookie_access_token_name = "materia_at";
                cookie_refresh_token_name = "materia_rt";
              };
            };

            oauth2 = mkOption {
              type = types.submodule {
                options = {
                  enabled = mkOption {
                    type = types.bool;
                  };
                  jwt_signing_algo = mkOption {
                    type = types.str;
                  };
                  jwt_singing_key = mkOption {
                    type = types.nullOr (types.oneOf [types.str types.path]);
                  };
                  jwt_secret = mkOption {
                    type = types.nullOr (types.oneOf [types.str types.path]);
                  };
                  access_token_lifetime = mkOption {
                    type = types.int;
                  };
                  refresh_token_lifetime = mkOption {
                    type = types.int;
                  };
                };
              };
              default = {
                enabled = true;
                jwt_signing_algo = "HS256";
                jwt_singing_key = null;
                jwt_secret = "changeme";
                access_token_lifetime = 3600;
                refresh_token_lifetime = 730 * 60;
              };
            };

            mailer = mkOption {
              type = types.submodule {
                options = {
                  enabled = mkOption {
                    type = types.bool;
                    default = false;
                  };
                  scheme = mkOption {
                    type = types.nullOr types.str;
                    default = null;
                  };
                  address = mkOption {
                    type = types.nullOr types.str;
                    default = null;
                  };
                  port = mkOption {
                    type = types.nullOr types.int;
                    default = null;
                  };
                  helo = mkOption {
                    type = types.bool;
                    default = true;
                  };
                  cert_file = mkOption {
                    type = types.nullOr types.path;
                    default = null;
                  };
                  key_file = mkOption {
                    type = types.nullOr types.path;
                    default = null;
                  };
                  sender = mkOption {
                    type = types.nullOr types.str;
                    default = null;
                  };
                  user = mkOption {
                    type = types.nullOr types.str;
                    default = null;
                  };
                  password = mkOption {
                    type = types.nullOr (types.oneOf [types.str types.path]);
                    default = null;
                  };
                  plain_text = mkOption {
                    type = types.bool;
                    default = false;
                  };
                };
              };
              default = {};
            };

            cron = mkOption {
              type = types.submodule {
                options = {
                  workers_count = mkOption {
                    type = types.int;
                  };
                };
              };
              default = {
                workers_count = 1;
              };
            };

            repository = mkOption {
              type = types.submodule {
                options = {
                  capacity = mkOption {
                    type = types.int;
                  };
                };
              };
              default = {capacity = 5368709120;};
            };

            misc = mkOption {
              type = types.submodule {
                options = {
                  enable_client = mkOption {
                    type = types.bool;
                  };
                  enable_docs = mkOption {
                    type = types.bool;
                  };
                  enable_api_docs = mkOption {
                    type = types.bool;
                  };
                };
              };
              default = {
                enable_client = true;
                enable_docs = true;
                enable_api_docs = false;
              };
            };
          };

          config = mkIf cfg.enable {
            users.users.materia = {
              description = "Materia service user";
              home = cfg.application.working_directory;
              createHome = true;
              isSystemUser = true;
              group = "materia";
            };
            users.groups.materia = {};

            systemd.services.materia = {
              description = "Materia service";
              wantedBy = ["multi-user.target"];
              after = ["network.target"];

              serviceConfig = {
                Restart = "always";
                ExecStart = "${lib.getExe cfg.package} start";
                User = "materia";
                WorkingDirectory = cfg.application.working_directory;
              };

              preStart = let
                toTOML = nix-std.lib.serde.toTOML;
                configFile = pkgs.writeText "config.toml" ''
                  ${toTOML {inherit (cfg) application server database cache security oauth2 mailer cron repository misc;}}
                '';
              in ''
                ln -sf ${configFile} ${cfg.application.working_directory}/config.toml
              '';
            };
          };
        };
    };

    nixosConfigurations.materia = nixpkgs.lib.nixosSystem {
      system = "x86_64-linux";
      modules = [
        self.nixosModules.materia
        ({
          pkgs,
          config,
          ...
        }: {
          boot.isContainer = true;

          networking.hostName = "materia";
          networking.useDHCP = false;

          services.redis.servers.materia = {
            enable = true;
            port = 6379;
            databases = 1;
          };

          services.postgresql = {
            enable = true;
            enableTCPIP = true;
            authentication = ''
              host        materia         all    127.0.0.1/32      trust
            '';
            initialScript = pkgs.writeText "init" ''
              CREATE ROLE materia WITH LOGIN PASSWORD 'test';
              CREATE DATABASE materia OWNER materia;
            '';
            ensureDatabases = ["materia"];
          };

          services.materia = {
            enable = true;
            cache.port = config.services.redis.servers.materia.port;
            database.password = "test";
          };

          system.stateVersion = "24.05";
        })
      ];
    };
  };
}
