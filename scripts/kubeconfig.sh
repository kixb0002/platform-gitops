#!/usr/bin/env bash
# À sourcer : stockage Linux privé, hors du montage Windows /mnt/c.
runtime_dir="/tmp/gitops-aks-$(id -u)"
if [[ -L "$runtime_dir" || ( -e "$runtime_dir" && ( ! -d "$runtime_dir" || ! -O "$runtime_dir" ) ) ]]; then
  echo 'Répertoire kubeconfig non sûr.' >&2
  exit 1
fi
mkdir -p -m 700 "$runtime_dir"
chmod 700 "$runtime_dir"
export KUBECONFIG="$runtime_dir/config"
if [[ -L "$KUBECONFIG" ]]; then
  echo 'Lien symbolique kubeconfig refusé.' >&2
  exit 1
fi
