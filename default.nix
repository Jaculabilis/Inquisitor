{ pkgs ? import (fetchTarball "https://github.com/NixOS/nixpkgs/archive/405d762a1a05ffed2ac820eb4bae4bc49bc3abf2.tar.gz") {}
}:

let
  app = pkgs.poetry2nix.mkPoetryApplication {
    projectDir = ./.;
  };
in app.dependencyEnv
