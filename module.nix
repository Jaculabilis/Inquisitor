flake: { config, lib, pkgs, ... }:

let
  inherit (lib) mkIf mkOption types;

  cfg = config.services.inquisitor;
in
{
  options = {
    services.inquisitor = {
      enable = mkOption {
        type = types.bool;
        default = true;
        description = "Enable the Inquisitor aggregator.";
      };

      listen.addr = mkOption {
        type = types.str;
        default = "0.0.0.0";
        description = "Listen address passed to nginx.";
      };

      listen.port = mkOption {
        type = types.port;
        default = 80;
        description = "Listen port passed to nginx.";
      };
    };
  };

  config =
  let
    # Get the inquisitor package from the flake.
    inquisitor = flake.packages.${pkgs.stdenv.hostPlatform.system}.env;

    # Define the inquisitor state directory.
    stateDir = "/var/lib/inquisitor";

    # Define an scp helper for item callbacks to use.
    scp-helper = pkgs.writeShellScriptBin "scp-helper" ''
      ${pkgs.openssh}/bin/scp -i ${stateDir}/.ssh/inquisitor.key -oStrictHostKeyChecking=no "$@"
    '';

    # Define the inquisitor service user.
    svcUser = {
      name = "inquisitor";
      group = "inquisitor";
      description = "Inquisitor service user";
      isSystemUser = true;
      shell = pkgs.bashInteractive;
      packages = [ inquisitor pkgs.cron ];
    };

    # Create a config file pointing to the state directory.
    inqConfig = pkgs.writeTextFile {
      name = "inquisitor.conf";
      text = ''
        DataPath = ${stateDir}/data/
        SourcePath = ${stateDir}/sources/
        CachePath = ${stateDir}/cache/
        Verbose = false
        LogFile = ${stateDir}/inquisitor.log
      '';
    };

    # Create a setup script to ensure the service directory state.
    inqSetup = pkgs.writeShellScript "inquisitor-setup.sh" ''
      # Ensure the required directories exist.
      ${pkgs.coreutils}/bin/mkdir -p ${stateDir}/data/inquisitor/
      ${pkgs.coreutils}/bin/mkdir -p ${stateDir}/sources/
      ${pkgs.coreutils}/bin/mkdir -p ${stateDir}/cache/
      if [ ! -f ${stateDir}/data/inquisitor/state ]; then
        ${pkgs.coreutils}/bin/echo "{}" > ${stateDir}/data/inquisitor/state
      fi

      # Ensure the service owns the folders.
      ${pkgs.coreutils}/bin/chown -R ${svcUser.name} ${stateDir}

      # Ensure the scp helper is present
      if [ -f ${stateDir}/scp-helper ]; then
        ${pkgs.coreutils}/bin/rm ${stateDir}/scp-helper
      fi
      ln -s -t ${stateDir} ${scp-helper}/bin/scp-helper
    '';

    # Create a run script for the service.
    inqRun = pkgs.writeShellScript "inquisitor-run.sh" ''
      cd ${stateDir}
      ${inquisitor}/bin/gunicorn \
        --bind=localhost:24133 \
        --workers=4 \
        --timeout 120 \
        --log-level debug \
        "inquisitor.app:wsgi()"
    '';

    # Create a wrapper to execute the cli as the service user.
    # (needed to avoid creating files in the state dir the service can't read)
    inqWrapper = pkgs.writeShellScriptBin "inq" ''
      sudo --user=${svcUser.name} ${inquisitor}/bin/inquisitor "$@"
    '';
  in mkIf cfg.enable
  {
    users.users.inquisitor = svcUser;
    users.groups.inquisitor = {};

    # Link the config in /etc to avoid envvar shenanigans
    environment.etc."inquisitor.conf".source = inqConfig;

    # Give all users the wrapper program.
    environment.systemPackages = [ inqWrapper ];
    # Allow the sudo in the cli wrapper without password.
    security.sudo.extraRules = [{
      commands = [{
        command = "${inquisitor}/bin/inquisitor";
        options = [ "NOPASSWD" ];
      }];
      runAs = svcUser.name;
      groups = [ "users" ];
    }];

    # Run the setup script on activation.
    system.activationScripts.inquisitorSetup = "${inqSetup}";

    # Set up the inquisitor service.
    systemd.services.inquisitor = {
      description = "Inquisitor server";
      script = "${inqRun}";
      serviceConfig = {
        User = svcUser.name;
        Type = "simple";
      };
      wantedBy = [ "multi-user.target" ];
      after = [ "network.target" ];
      enable = true;
    };

    # Set up the nginx reverse proxy to the server.
    services.nginx.enable = true;
    services.nginx.virtualHosts.inquisitorHost = {
      listen = [ cfg.listen ];
      locations."/".extraConfig = ''
        access_log /var/log/nginx/access.inquisitor.log;
        proxy_buffering off;
        proxy_pass http://localhost:24133/;
      '';
    };
    networking.firewall.allowedTCPPorts = [ cfg.listen.port ];

    # Enable cron so the service can use it to schedule fetches.
    services.cron.enable = true;
  };
}

