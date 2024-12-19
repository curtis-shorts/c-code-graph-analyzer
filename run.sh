run_dir='/Users/cushorts/workspace/elec876/antlr_project/github_test/csource-graph-plotter'
cd $run_dir
extra_flags=( '--functions_only 0' '--functions_only 1' '--macros_only 1' )
projects=( 'ucx' 'ofi' 'sos' 'portals' 'mpi' ) 
project=${projects[0]}

# Use the following bash command to get your run_dirs and remove those you don't want:
#       ls -l $source_dir | egrep '^d' | awk '{printf "\047" $NF "\047 " }; END {printf "\n"}'
# Note that out_dir and source_dir need to end in /
if [[ $project == 'ucx' ]]; then
    out_dir="${run_dir}/outputs/"
    source_dir='/Users/cushorts/workspace/elec876/antlr_project/ucx/src/'
    run_dirs=("uct" "ucs" "ucp")
elif [[ $project == 'ofi' ]]; then
    out_dir="${run_dir}/outputs/"
    source_dir='/Users/cushorts/workspace/elec876/antlr_project/libfabric/'
    run_dirs=('include' 'src' 'util' 'prov' 'fabtests')
elif [[ $project == 'portals' ]]; then
    out_dir="${run_dir}/outputs/"
    source_dir='/Users/cushorts/workspace/elec876/antlr_project/portals4/'
    run_dirs=( 'src' 'include' )
else
    echo "ERROR: Unkown project specified - $project"
    exit
fi

# Run everything
for extra_flag in "${extra_flags[@]}"; do
    # Run the cluster generation
    for algorithm in `seq 0 3`; do
        echo "Running $project with algorithm $algorithm, extra flags: $extra_flag"
        python ./main.py -s $source_dir -o $out_dir -p $project --random_samples 1 \
                -d ${run_dirs[@]} -a $algorithm $extra_flag
    done
done

# Remove empty output directories
find $out_dir -type d -empty -delete

