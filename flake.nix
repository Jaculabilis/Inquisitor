{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs?ref=refs/tags/22.11";
    flake-compat = {
      url = "github:edolstra/flake-compat";
      flake = false;
    };
  };

  outputs = { self, nixpkgs, flake-compat }:
  let
    system = "x86_64-linux";
    pkgs = nixpkgs.legacyPackages.${system};
  in
  {
    packages.${system}.default =
      (pkgs.poetry2nix.mkPoetryApplication {
        projectDir = ./.;
      }).dependencyEnv;

    defaultPackage.${system} = self.packages.${system}.default;

    devShell.${system} = pkgs.mkShell {
      buildInputs = [ (pkgs.python3.withPackages (p: [p.poetry])) ];
    };
  };
}
