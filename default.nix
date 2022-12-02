{ pkgs ? import (fetchTarball "https://github.com/NixOS/nixpkgs/archive/2ebb6c1e5ae402ba35cca5eec58385e5f1adea04.tar.gz") {}
}:

let
  app = pkgs.poetry2nix.mkPoetryApplication {
    projectDir = ./.;
  };
in app.dependencyEnv
