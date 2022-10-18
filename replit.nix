{ pkgs }: with pkgs; {
  deps = with python310Packages; [
    python-lsp-black
    poetry
  ];
  env = {
    PYTHON_LD_LIBRARY_PATH = lib.makeLibraryPath [
      # Needed for pandas / numpy
      stdenv.cc.cc.lib
      zlib
      # Needed for pygame
      glib
      # Needed for matplotlib
      xorg.libX11
    ];
    PYTHONBIN = "${python310}/bin/python3.10";
    LANG = "en_US.UTF-8";
  };
}