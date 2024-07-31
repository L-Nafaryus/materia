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
          version = "0.0.1";

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

          pdm.lockfile = ./materia-web-client/pdm.lock;
          pdm.pyproject = ./materia-web-client/pyproject.toml;

          deps = _: {
            python = pkgs.python3;
          };

          mkDerivation = {
            src = ./workspaces/frontend;
            buildInputs = [
              pkgs.python3.pkgs.pdm-backend
            ];
            configurePhase = ''
              cp -rv ${materia-frontend-nodejs}/dist ./src/materia-frontend/
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

      materia-server = dreamBuildPackage {
        module = {
          config,
          lib,
          dream2nix,
          materia-frontend,
          ...
        }: {
          imports = [dream2nix.modules.dream2nix.WIP-python-pdm];

          pdm.lockfile = ./materia-server/pdm.lock;
          pdm.pyproject = ./materia-server/pyproject.toml;

          deps = _: {
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
          maintainers = with bonLib.maintainers; [L-Nafaryus];
          broken = false;
          mainProgram = "materia-server";
        };
      };

      postgresql-devel = bonfire.packages.x86_64-linux.postgresql;

      redis-devel = bonfire.packages.x86_64-linux.redis;
    };

    apps.x86_64-linux = {
      materia-server = {
        type = "app";
        program = "${self.packages.x86_64-linux.materia-server}/bin/materia-server";
      };
    };

    devShells.x86_64-linux.default = pkgs.mkShell {
      buildInputs = with pkgs; [postgresql redis pdm nodejs];
      # greenlet requires libstdc++
      LD_LIBRARY_PATH = nixpkgs.lib.makeLibraryPath [pkgs.stdenv.cc.cc];
    };
  };
}
