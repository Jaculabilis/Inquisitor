{
  inputs = {
    my-flake.url = "github:Jaculabilis/my-flake";
    nixpkgs.url = "github:NixOS/nixpkgs?ref=refs/tags/22.11";
    flake-compat = {
      url = "github:edolstra/flake-compat";
      flake = false;
    };
  };

  outputs = { self, my-flake, nixpkgs, flake-compat }:
  let
    systems = [ "aarch64-linux" "x86_64-linux" ];
    each = system:
    let
      pkgs = (import nixpkgs {
        inherit system;
        overlays = [ self.overlays.default ];
      });
    in {
      packages.${system} = {
        default = self.packages.${system}.inquisitor;
        inquisitor = pkgs.inquisitor;
        env = pkgs.inquisitor.dependencyEnv;
      };

      devShells.${system} = {
        default = self.devShells.${system}.inquisitor;
        inquisitor = pkgs.mkShell {
          buildInputs = [ (pkgs.python3.withPackages (p: [p.poetry])) ];
          shellHook = ''
            PS1="(inquisitor) $PS1"
          '';
        };
        sources = pkgs.mkShell {
          buildInputs = [ self.packages.${system}.env ];
          shellHook = ''
            PS1="(sources) $PS1"
          '';
        };
      };
    };
  in (my-flake.outputs-for each systems) // {
    overlays.default = final: prev: {
      inquisitor = final.poetry2nix.mkPoetryApplication {
        projectDir = ./.;
      };
    };
  };
}
