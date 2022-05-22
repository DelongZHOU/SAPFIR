#!/bin/bash
#SBATCH --time=10:00:00
#SBATCH --output=%u.%x-%A[%a].out
#SBATCH --mem=128000M
#SBATCH --cpus-per-task=32
#SBATCH --array=0-115
#SBATCH --mail-type=ALL
#SBATCH --mail-user=
module load interproscan
id_3d=$(printf %03d $SLURM_ARRAY_TASK_ID)

cd $SLURM_TMPDIR
mkdir array_sample
cd array_sample
cp ~/path/to/fasta/hsa.38.${id_3d}.fa .
interproscan.sh -i hsa.38.${id_3d}.fa -f tsv -dp -cpu 32 > hsa.38.${id_3d}.log
mv hsa.38.${id_3d}.log ~/path/to/log/
mv hsa.38.${id_3d}.fa.tsv ~/path/to/result/
