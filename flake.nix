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
      materia-frontend-nodejs = dreamBuildPackage {
        module = {
          lib,
          config,
          dream2nix,
          ...
        }: {
          name = "materia-frontend";
          version = "0.0.5";

          imports = [
            dream2nix.modules.dream2nix.WIP-nodejs-builder-v3
          ];

          mkDerivation = {
            src = ./workspaces/frontend;
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
          inherit (self.packages.x86_64-linux) materia-frontend-nodejs;
        };
        module = {
          config,
          lib,
          dream2nix,
          materia-frontend-nodejs,
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
              cp -rv ${materia-frontend-nodejs}/dist ./src/materia_frontend/
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
    };

    devShells.x86_64-linux.default = pkgs.mkShell {
      buildInputs = with pkgs; [postgresql redis pdm nodejs python312];
      # greenlet requires libstdc++
      LD_LIBRARY_PATH = nixpkgs.lib.makeLibraryPath [pkgs.stdenv.cc.cc];
    };
  };
}
