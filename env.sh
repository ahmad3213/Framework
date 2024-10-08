#!/usr/bin/env bash

run_cmd() {
  echo "> $@"
  "$@"
  RESULT=$?
  if (( $RESULT != 0 )); then
    echo "Error while running '$@'"
    kill -INT $$
  fi
}

get_os_prefix() {
  local os_version=$1
  local for_global_tag=$2
  if (( $os_version >= 8 )); then
    echo el
  elif (( $os_version < 6 )); then
    echo error
  else
    if [[ $for_global_tag == 1 || $os_version == 6 ]]; then
      echo slc
    else
      echo cc
    fi
  fi
}

do_install_cmssw() {
  local this_file="$( [ ! -z "$ZSH_VERSION" ] && echo "${(%):-%x}" || echo "${BASH_SOURCE[0]}" )"
  local this_dir="$( cd "$( dirname "$this_file" )" && pwd )"

  export SCRAM_ARCH=$1
  local CMSSW_VER=$2
  local cmb_version=$3
  if ! [ -f "$this_dir/soft/$CMSSW_VER/.installed" ]; then
    run_cmd mkdir -p "$this_dir/soft"
    run_cmd cd "$this_dir/soft"
    run_cmd source /cvmfs/cms.cern.ch/cmsset_default.sh
    if [ -d $CMSSW_VER ]; then
      echo "Removing incomplete $CMSSW_VER installation..."
      run_cmd rm -rf $CMSSW_VER
    fi
    echo "Creating $CMSSW_VER area for in $PWD ..."
    run_cmd scramv1 project CMSSW $CMSSW_VER
    run_cmd cd $CMSSW_VER/src
    eval `scramv1 runtime -sh`
    run_cmd mkdir -p HHTools
    run_cmd ln -s "$this_dir/HHbtag" HHTools/HHbtag
    run_cmd mkdir -p TauAnalysis
    run_cmd ln -s "$this_dir/ClassicSVfit" TauAnalysis/ClassicSVfit
    run_cmd ln -s "$this_dir/SVfitTF" TauAnalysis/SVfitTF
    run_cmd mkdir -p HHKinFit2
    run_cmd ln -s "$this_dir/HHKinFit2" HHKinFit2/HHKinFit2
    if [ "$cmb_version" != "none" ]; then
      run_cmd git clone https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit.git HiggsAnalysis/CombinedLimit
      run_cmd cd HiggsAnalysis/CombinedLimit
      run_cmd git checkout $cmb_version
      run_cmd cd ../..
      run_cmd git clone https://github.com/cms-analysis/CombineHarvester.git CombineHarvester
    fi
    run_cmd scram b -j8
    run_cmd touch "$this_dir/soft/$CMSSW_VER/.installed"
  fi
}

do_install_inference() {
  local this_file="$( [ ! -z "$ZSH_VERSION" ] && echo "${(%):-%x}" || echo "${BASH_SOURCE[0]}" )"
  local this_dir="$( cd "$( dirname "$this_file" )" && pwd )"

  local cmb_version=$1
  export ANALYSIS_PATH="$this_dir"

  local setups_dir="$this_dir/inference/.setups"
  local setup_file="$setups_dir/flaf.sh"

  if ! [ -f "$setup_file" ]; then
    run_cmd mkdir -p "$setups_dir"
    cat > "$setup_file" <<EOF
export DHI_USER="$(whoami)"
export DHI_USER_FIRSTCHAR="\${DHI_USER:0:1}"
export DHI_DATA="\$ANALYSIS_PATH/inference/data"
export DHI_STORE="\$DHI_DATA/store"
export DHI_STORE_JOBS="\$DHI_STORE"
export DHI_STORE_BUNDLES="\$DHI_STORE"
export DHI_STORE_EOSUSER="/eos/user/\$DHI_USER_FIRSTCHAR/\$DHI_USER/dhi/store"
export DHI_SOFTWARE="\$DHI_DATA/software"
export DHI_WLCG_USE_CACHE="false"
export DHI_LOCAL_SCHEDULER="True"
export DHI_SCHEDULER_HOST="hh:cmshhcombr2@hh-scheduler1.cern.ch"
export DHI_SCHEDULER_PORT="80"
export DHI_COMBINE_VERSION="$cmb_version"
EOF
  fi

  run_cmd mkdir -p "$this_dir/soft/bin"
  if ! [ -f "$this_dir/soft/bin/combine" ]; then
    run_cmd ln -s "$this_dir/run_tools/cmsExe.sh" "$this_dir/soft/bin/combine"
  fi
  if ! [ -f "$this_dir/soft/bin/text2workspace.py" ]; then
    run_cmd ln -s "$this_dir/run_tools/cmsExe.sh" "$this_dir/soft/bin/text2workspace.py"
  fi

  run_cmd mkdir -p "$this_dir/inference/data"
  run_cmd touch "$this_dir/inference/data/.installed"
}

install() {
  local this_file="$( [ ! -z "$ZSH_VERSION" ] && echo "${(%):-%x}" || echo "${BASH_SOURCE[0]}" )"
  local this_dir="$( cd "$( dirname "$this_file" )" && pwd )"
  local node_os=$1
  local target_os=$2
  local cmd_to_run=$3
  local installed_flag=$4

  if [ -f "$this_dir/$installed_flag" ]; then
    return 0
  fi

  if [[ $node_os == $target_os ]]; then
    local env_cmd=""
    local env_cmd_args=""
  else
    local env_cmd="cmssw-$target_os"
    if ! command -v $env_cmd &> /dev/null; then
      echo "Unable to do a cross-platform installation. $env_cmd is not available."
      return 1
    fi
    local env_cmd_args="--command-to-run"
  fi

  run_cmd $env_cmd $env_cmd_args /usr/bin/env -i HOME=$HOME bash "$this_file" $cmd_to_run "${@:5}"
}

install_cmssw() {
  local node_os=$1
  local target_os=$2
  local scram_arch=$3
  local cmssw_version=$4
  local cmb_ver=$5
  install $node_os $target_os install_cmssw "soft/$cmssw_version/.installed" "$scram_arch" "$cmssw_version" "$cmb_ver"
}

install_inference() {
  local node_os=$1
  local target_os=$2
  local cmb_ver=$3
  install $node_os $target_os install_inference "inference/data/.installed" $cmb_ver
}

action() {
  # determine the directory of this file
  local this_file="$( [ ! -z "$ZSH_VERSION" ] && echo "${(%):-%x}" || echo "${BASH_SOURCE[0]}" )"
  local this_dir="$( cd "$( dirname "$this_file" )" && pwd )"

  export PYTHONPATH="$this_dir:$this_dir/inference:$PYTHONPATH"
  export LAW_HOME="$this_dir/.law"
  export LAW_CONFIG_FILE="$this_dir/config/law.cfg"

  export ANALYSIS_PATH="$this_dir"
  export ANALYSIS_DATA_PATH="$ANALYSIS_PATH/data"
  export X509_USER_PROXY="$ANALYSIS_DATA_PATH/voms.proxy"

  if ! [ -d "$ANALYSIS_DATA_PATH" ]; then
    run_cmd mkdir -p "$ANALYSIS_DATA_PATH"
  fi

  local os_version=$(cat /etc/os-release | grep VERSION_ID | sed -E 's/VERSION_ID="([0-9]+).*"/\1/')
  local os_prefix=$(get_os_prefix $os_version)
  local node_os=$os_prefix$os_version

  local flaf_cmssw_ver=CMSSW_14_1_0_pre6
  local target_os_version=9
  local target_os_prefix=$(get_os_prefix $target_os_version)
  local target_os_gt_prefix=$(get_os_prefix $target_os_version 1)
  local target_os=$target_os_prefix$target_os_version
  local cmb_ver="v10.0.2"
  export FLAF_CMSSW_BASE="$ANALYSIS_PATH/soft/$flaf_cmssw_ver"
  export FLAF_CMSSW_ARCH="${target_os_gt_prefix}${target_os_version}_amd64_gcc12"
  install_cmssw $node_os $target_os $FLAF_CMSSW_ARCH $flaf_cmssw_ver $cmb_ver

  local cmb_cmssw_ver=$flaf_cmssw_ver
  local cmb_scram_arch=$FLAF_CMSSW_ARCH

  local cmb_os_version=9
  local cmb_os_prefix=$(get_os_prefix $cmb_os_version)
  local cmb_os=$cmb_os_prefix$cmb_os_version
  install_inference $node_os $cmb_os $cmb_ver
  if [ ! -z $ZSH_VERSION ]; then
    autoload bashcompinit
    bashcompinit
  fi
  source /afs/cern.ch/work/k/kandroso/public/flaf_env_2024_08/bin/activate
  source "$( law completion )"
  source /cvmfs/cms.cern.ch/rucio/setup-py3.sh &> /dev/null
  source $ANALYSIS_PATH/inference/.setups/flaf.sh
  export PATH=$ANALYSIS_PATH/soft/bin:$PATH
  alias cmsEnv="env -i HOME=$HOME ANALYSIS_PATH=$ANALYSIS_PATH ANALYSIS_DATA_PATH=$ANALYSIS_DATA_PATH X509_USER_PROXY=$X509_USER_PROXY CENTRAL_STORAGE=$CENTRAL_STORAGE ANALYSIS_BIG_DATA_PATH=$ANALYSIS_BIG_DATA_PATH FLAF_CMSSW_BASE=$FLAF_CMSSW_BASE FLAF_CMSSW_ARCH=$FLAF_CMSSW_ARCH $ANALYSIS_PATH/cmsEnv.sh"
}

if [ "X$1" = "Xinstall_cmssw" ]; then
  do_install_cmssw "${@:2}"
elif [ "X$1" = "Xinstall_inference" ]; then
  do_install_inference "${@:2}"
else
  action "$@"
fi
