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
        forAllSystems = nixpkgs.lib.genAttrs [ "x86_64-linux" ];
        nixpkgsFor = forAllSystems (system: import nixpkgs { inherit system; });
    in
    {
        packages = forAllSystems (system: let
            pkgs = nixpkgsFor.${system};
            inherit (poetry2nix.lib.mkPoetry2Nix { inherit pkgs; }) mkPoetryApplication;
        in {
            materia = mkPoetryApplication { 
                projectDir = ./.; 
            };

            default = self.packages.${system}.materia;
        });

        apps = forAllSystems (system: {
            materia = {
                type = "app";
                program = "${self.packages.${system}.materia}/bin/materia";
            };

            default = self.apps.${system}.materia;
        });

        devShells = forAllSystems (system: let 
            pkgs = nixpkgsFor.${system};
            db_name = "materia";
            db_user = "materia";
            db_path = "temp/materia-db";
        in {
            default = pkgs.mkShell {
                buildInputs = with pkgs; [ 
                    nil 
                    nodejs
                    ripgrep

                    postgresql

                    poetry
                ];

                LD_LIBRARY_PATH = nixpkgs.lib.makeLibraryPath [ pkgs.stdenv.cc.cc ];

                shellHook = ''
                    trap "pg_ctl -D ${db_path} stop" EXIT

                    [ ! -d $(pwd)/${db_path} ] && initdb -D $(pwd)/${db_path} -U ${db_user}
                    pg_ctl -D $(pwd)/${db_path} -l $(pwd)/${db_path}/db.log -o "--unix_socket_directories=$(pwd)/${db_path}" start
                    [ ! "$(psql -h $(pwd)/${db_path} -U ${db_user} -l | rg '^ ${db_name}')" ] && createdb -h $(pwd)/${db_path} -U ${db_user} ${db_name}
                '';
            };
        });

    };

}
