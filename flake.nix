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

  outputs = {
    self,
    nixpkgs,
    dream2nix,
    bonfire,
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
      materia-server = dreamBuildPackage {
        module = {
          config,
          lib,
          dream2nix,
          ...
        }: {
          imports = [dream2nix.modules.dream2nix.WIP-python-pdm];

          pdm.lockfile = ./pdm.lock;
          pdm.pyproject = ./pyproject.toml;

          deps = _: {
            python = pkgs.python312;
          };

          mkDerivation = {
            src = ./.;
            buildInputs = [
              pkgs.python312.pkgs.pdm-backend
            ];
            nativeBuildInputs = [
              pkgs.python312.pkgs.wrapPython
            ];
            configurePhase = ''
              ${lib.getExe pkgs.mkdocs} build -d src/materia/docs/
            '';
            # TODO: include docs
          };
        };
        meta = with nixpkgs.lib; {
          description = "Materia";
          license = licenses.mit;
          maintainers = with bonLib.maintainers; [L-Nafaryus];
          broken = false;
          mainProgram = "materia";
        };
      };

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
            src = ./workspaces/frontend;
            configurePhase = ''
              ${self.packages.x86_64-linux.materia-server}/bin/materia export openapi --path ./
              npm run openapi
            '';
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
          description = "Materia frontend (nodejs)";
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

          pdm.lockfile = ./workspaces/frontend/pdm.lock;
          pdm.pyproject = ./workspaces/frontend/pyproject.toml;

          deps = _: {
            python = pkgs.python312;
          };

          mkDerivation = {
            src = ./workspaces/frontend;
            buildInputs = [
              pkgs.python312.pkgs.pdm-backend
            ];
            configurePhase = ''
              cp -rv ${materia-frontend-vue}/dist ./src/materia_frontend/
            '';
          };
        };
        meta = with nixpkgs.lib; {
          description = "Materia frontend";
          license = licenses.mit;
          maintainers = with bonLib.maintainers; [L-Nafaryus];
          broken = false;
        };
      };

      materia = dreamBuildPackage {
        extraArgs = {
          inherit (self.packages.x86_64-linux) materia-frontend;
        };
        module = {
          config,
          lib,
          dream2nix,
          materia-frontend,
          ...
        }: {
          imports = [dream2nix.modules.dream2nix.WIP-python-pdm];

          pdm.lockfile = ./pdm.lock;
          pdm.pyproject = ./pyproject.toml;

          deps = _: {
            python = pkgs.python312;
          };

          mkDerivation = {
            src = ./.;
            buildInputs = [
              pkgs.python312.pkgs.pdm-backend
            ];
            nativeBuildInputs = [
              pkgs.python312.pkgs.wrapPython
            ];
            propagatedBuildInputs = [
              materia-frontend
            ];
          };
        };
        meta = with nixpkgs.lib; {
          description = "Materia";
          license = licenses.mit;
          maintainers = with bonLib.maintainers; [L-Nafaryus];
          broken = false;
          mainProgram = "materia";
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
              self.packages.x86_64-linux.materia
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
  };
}
