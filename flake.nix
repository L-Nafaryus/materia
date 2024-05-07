{
    description = "Materia is a file server";

    nixConfig = {
        extra-substituters = [ "https://bonfire.cachix.org" ];
        extra-trusted-public-keys = [ "bonfire.cachix.org-1:mzAGBy/Crdf8NhKail5ciK7ZrGRbPJJobW6TwFb7WYM=" ];
    };

    inputs = {
        nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
        poetry2nix = {
            url = "github:nix-community/poetry2nix";
            inputs.nixpkgs.follows = "nixpkgs";
        };
    };

    outputs = { self, nixpkgs, poetry2nix, ... }:
    let
        #perSystem = systems: builtins.mapAttrs (name: value: nixpkgs.lib.genAttrs systems (system: value) );
        forAllSystems = nixpkgs.lib.genAttrs [ "x86_64-linux" ];
        nixpkgsFor = forAllSystems (system: import nixpkgs { inherit system; });
    in
    {
        apps = forAllSystems (system:
        let 
            pkgs = nixpkgsFor.${system};
            app = (poetry2nix.lib.mkPoetry2Nix { inherit pkgs; }).mkPoetryApplication { projectDir = ./.; };
        in rec {
            materia = {
                type = "app";
                program = "${app}/bin/materia";
            };

            default = materia;
        });

        devShells = forAllSystems (system: 
        let pkgs = nixpkgsFor.${system};
        in {
            default = pkgs.mkShell {
                buildInputs = [ 
                    pkgs.poetry
                    pkgs.nil 
                    pkgs.nodejs
                ];
            };
        });

    };

}
