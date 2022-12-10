{ pkgs ? import (fetchTarball "https://github.com/NixOS/nixpkgs/archive/2ebb6c1e5ae402ba35cca5eec58385e5f1adea04.tar.gz") {}
}:

pkgs.mkShell {
  buildInputs = [
    (pkgs.python3.withPackages (p: [p.poetry]))
  ];
}
