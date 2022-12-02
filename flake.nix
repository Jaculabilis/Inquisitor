{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs?rev=2ebb6c1e5ae402ba35cca5eec58385e5f1adea04";
  };

  outputs = { self, nixpkgs }:
  {
    packages."x86_64-linux".default =
      let
        pkgs = nixpkgs.legacyPackages."x86_64-linux";
      in pkgs.callPackage ./default.nix {};
  };
}
