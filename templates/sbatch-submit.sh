#!/bin/bash

#SBATCH --job-name="<EXE>"
#SBATCH -p <PARTITION>
#SBATCH -t <TIME>
#SBATCH -N 1
#SBATCH -c <CORES>

source /etc/profile.d/modules.sh

module load intel/2020.4
module load intelmpi/intel/2019.6
module load python/3.6.8
module remove gcc
module load gcc/9.3.0

# export OMP_NUM_THREADS=$SLURM_JOB_CPUS_PER_NODE
export OMP_NUM_THREADS=<CORES>
export OMP_TOOL_LIBRARIES=/ddn/home/<USER>/dissertation/otter/lib/<LIB>

# Otter environment variables
export OTTER_TASK_GRAPH_OUTPUT="<ROOT>/<EXPERIMENT>/task-graph"
export OTTER_TASK_GRAPH_FORMAT=dot
export OTTER_TASK_GRAPH_NODEATTR=peano-tasks.json
export OTTER_APPEND_HOSTNAME

cd <ROOT>/<EXPERIMENT>
<ROOT>/<EXPERIMENT>/<EXE> 2>stderr.log 1>/dev/null

dot -Tpdf -o $OTTER_TASK_GRAPH_OUTPUT.pdf -Kdot $OTTER_TASK_GRAPH_OUTPUT.gv
