{
    description = "Materia";

    inputs = { 
        nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
        dream2nix = { 
            url = "github:nix-community/dream2nix";
            inputs.nixpkgs.follows = "nixpkgs";
        };
        bonfire.url = "github:L-Nafaryus/bonfire";
    };


    outputs = { self, nixpkgs, dream2nix, bonfire, ... }:
    let
        system = "x86_64-linux";
        pkgs = import nixpkgs { inherit system; };
        bonpkgs = bonfire.packages.${system};
        bonlib = bonfire.lib;

        dreamBuildPackage = { module, meta ? {}, extraModules ? [], extraArgs ? {} }: (
            nixpkgs.lib.evalModules {
                modules = [ module ] ++ extraModules;
                specialArgs = {
                    inherit dream2nix;
                    packageSets.nixpkgs = pkgs;
                } // extraArgs; 
            }
        ).config.public // { inherit meta; };

    in
    {
        packages.x86_64-linux = {
            materia-frontend = dreamBuildPackage { 
                module = { lib, config, dream2nix, ... }: {
                    name = "materia-frontend";
                    version = "0.0.1";

                    imports = [
                        dream2nix.modules.dream2nix.WIP-nodejs-builder-v3
                    ];

                    mkDerivation = {
                        src = ./materia-web-client/src/materia-frontend;
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
                    description = "Materia frontend";
                    license = licenses.mit;
                    maintainers = with bonlib.maintainers; [ L-Nafaryus ];
                    broken = false;
                };
            };

            materia-web-client = dreamBuildPackage { 
                extraArgs = { 
                    inherit (self.packages.x86_64-linux) materia-frontend; 
                }; 
                module = {config, lib, dream2nix, materia-frontend, ...}: {
                    imports = [ dream2nix.modules.dream2nix.WIP-python-pdm ];

                    pdm.lockfile = ./materia-web-client/pdm.lock;
                    pdm.pyproject = ./materia-web-client/pyproject.toml;

                    deps = _ : {
                        python = pkgs.python3;
                    };

                    mkDerivation = {
                        src = ./materia-web-client;
                        buildInputs = [
                            pkgs.python3.pkgs.pdm-backend
                        ];
                        configurePhase = ''
                            cp -rv ${materia-frontend}/dist ./src/materia-frontend/
                        '';
                    };
                }; 
                meta = with nixpkgs.lib; {
                    description = "Materia web client";
                    license = licenses.mit;
                    maintainers = with bonlib.maintainers; [ L-Nafaryus ];
                    broken = false;
                };
            };

            materia-server = dreamBuildPackage { 
                module = {config, lib, dream2nix, materia-frontend, ...}: {
                    imports = [ dream2nix.modules.dream2nix.WIP-python-pdm ];

                    pdm.lockfile = ./materia-server/pdm.lock;
                    pdm.pyproject = ./materia-server/pyproject.toml;

                    deps = _ : {
                        python = pkgs.python3;
                    };

                    mkDerivation = {
                        src = ./materia-server;
                        buildInputs = [
                            pkgs.python3.pkgs.pdm-backend
                        ];
                        nativeBuildInputs = [
                            pkgs.python3.pkgs.wrapPython
                        ];
                        
                    };
                };
                meta = with nixpkgs.lib; {
                    description = "Materia";
                    license = licenses.mit;
                    maintainers = with bonlib.maintainers; [ L-Nafaryus ];
                    broken = false;
                    mainProgram = "materia-server";
                };
            };

            postgresql = let 
                user = "postgres";
                database = "postgres";
                dataDir = "/var/lib/postgresql";
                entryPoint = pkgs.writeTextDir "entrypoint.sh" ''
                    initdb -U ${user} 
                    postgres -k ${dataDir}
                '';
            in pkgs.dockerTools.buildImage {
                name = "postgresql";
                tag = "devel";

                copyToRoot = pkgs.buildEnv {
                    name = "image-root";
                    pathsToLink = [ "/bin" "/etc" "/" ];
                    paths = with pkgs; [
                        bash
                        postgresql
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
                    Entrypoint = [ "bash" "/entrypoint.sh" ];
                    StopSignal = "SIGINT";
                    User = "${user}:${user}";
                    Env = [ "PGDATA=${dataDir}" ];
                    WorkingDir = dataDir;
                    ExposedPorts = {
                        "5432/tcp" = {};
                    };
                };
            };

            redis = let 
                user = "redis";
                dataDir = "/var/lib/redis";
                entryPoint = pkgs.writeTextDir "entrypoint.sh" ''
                    redis-server \
                        --daemonize no \
                        --dir "${dataDir}"
                '';
            in pkgs.dockerTools.buildImage {
                name = "redis";
                tag = "devel";

                copyToRoot = pkgs.buildEnv {
                    name = "image-root";
                    pathsToLink = [ "/bin" "/etc" "/" ];
                    paths = with pkgs; [
                        bash
                        redis
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
                    Entrypoint = [ "bash" "/entrypoint.sh" ];
                    StopSignal = "SIGINT";
                    User = "${user}:${user}";
                    WorkingDir = dataDir;
                    ExposedPorts = {
                        "6379/tcp" = {};
                    };
                };
            };
        };

        apps.x86_64-linux = {
            materia-server = {
                type = "app";
                program = "${self.packages.x86_64-linux.materia-server}/bin/materia-server";
            };
        };

        devShells.x86_64-linux.default = pkgs.mkShell {
            buildInputs = with pkgs; [ postgresql redis ];
        };
    };
}
