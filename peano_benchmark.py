import argparse
import subprocess

def make_parser(default_args):
    parser = argparse.ArgumentParser(
        description='Prepare a Peano benchmark experiment with an OMPT tool attached',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    peano_args = parser.add_argument_group("Peano arguments")
    exp_args   = parser.add_argument_group("Experimental arguments")
    sbatch_args = parser.add_argument_group("SBATCH arguments")

    parser.add_argument('user', help='Hamilton username')

    exp_args.add_argument(
        '-l', '--lib', default=default_args['lib'], dest='lib',
        help='OMPT library to load at job start')

    exp_args.add_argument(
        '-ns', '--no-submit', action='store_true', dest='no_submit',
        help='If specified, stop before submitting the job with sbatch')

    # Experiment args
    exp_args.add_argument(
        '-r', '--root', default=default_args["experiment_root"],
        help='The root directory for this Peano4 benchmark experiment')
    
    peano_args.add_argument(
        '-p', '--peano', default=default_args["peano_root"],
        help='Root directory of ExaHyPE/Peano build')
    
    # Peano args
    exp_args.add_argument(
        '-m',  '--mode', default=default_args["mode"],
        choices=['release'],
        help='Build mode of the benchmark')
    
    exp_args.add_argument(
        '-t',  '--type', default=default_args["type"],
        choices=["default",'default-ats','enclave','enclave-ats'],
        help='Selected Peano4 variant')
    
    exp_args.add_argument(
        '-cs', '--cell-size', default=default_args["cs"],
        dest='cellsize',
        help='Absolute size of each grid cell division')
     
    exp_args.add_argument(
        '-d',  '--dim', type=int, default=default_args["dim"], choices=[2,3],
        help='Dimensions')
         
    exp_args.add_argument(
        '-ps', type=int, default=default_args["ps"],
        help='Number of volumes (patches) per grid cell')

    exp_args.add_argument(
        '-et', '--end-time', default=default_args["et"], 
        dest='endtime',
        help='Benchmark end time (seconds)')
    
    exp_args.add_argument(
        '-j',  '--parallel-builds', type=int, default=default_args["j"], 
        dest='j',
        help='Number of cores for building')

    exp_args.add_argument(
        '-x', '--postfix', dest='postfix', default="",
        help='String to append to the experiment directory'
    )

    # SBATCH args
        
    sbatch_args.add_argument(
        '-c', '--cores', type=int, default=default_args["cores"],
        dest='cores',
        help='Number of cores to request in slurm job'
    )
        
    sbatch_args.add_argument(
        '-par', '--partition', default=default_args["partition"],
        dest='partition',
        choices=["par6.q", "par7.q"],
        help='Partition to submit job to'
    )
        
    sbatch_args.add_argument(
        '-T', '--time', default=default_args["time"],
        dest='time',
        help='Wall-clock time limit for job [hh:mm:ss]'
    )

    return parser

def get_experiment_name(args):
    executable = f'{args["type"]}_{args["mode"]}_{args["dim"]}D'
    experiment = executable + "_" + args["timestamp"]
    if args["postfix"] not in ["", None]:
        experiment = experiment + "_" + args["postfix"]
    return experiment, executable

def create_remote_dir(args):

    # check that the root exists on Hamilton
    sshcmd = f"""ssh hamilton '[[ -d "{args["root"]}" ]] && echo 1'"""
    print(sshcmd)
    proc = subprocess.run(sshcmd, shell=True, capture_output=True, text=True)
    if proc.stdout.strip() == "":
        raise FileNotFoundError(args["root"])
    else:
        print("> Found: {}".format(args["root"]))

    # make the directory
    sshcmd = f"""ssh hamilton 'mkdir {args["root"]}/{args["experiment"]}'"""
    print(sshcmd)
    proc = subprocess.run(sshcmd, shell=True)
    if proc.returncode != 0:
        raise RuntimeError("error creating remote directory")

def generate_build_script(args):

    with open("templates/build.sh", "r") as f:
        buildsh = f.read()
    
    buildsh = buildsh.replace("<GENERATED>",  args["timestamp"])
    buildsh = buildsh.replace("<ROOT>",       args["root"])
    buildsh = buildsh.replace("<EXPERIMENT>", args["experiment"])
    buildsh = buildsh.replace("<PEANO>",      args["peano"])
    buildsh = buildsh.replace("<EXE>",        args["executable"])
    buildsh = buildsh.replace("<MODE>",       args["mode"])
    buildsh = buildsh.replace("<TYPE>",       args["type"])
    buildsh = buildsh.replace("<CELLSIZE>",   args["cellsize"])
    buildsh = buildsh.replace("<DIM>",        args["dim"])
    buildsh = buildsh.replace("<PS>",         args["ps"])
    buildsh = buildsh.replace("<ENDTIME>",    args["endtime"])
    buildsh = buildsh.replace("<J>",          args["j"])
    
    with open("build.sh", "w") as f:
        f.write(buildsh)

def build_experiment(args):
    
    scp(args['user'], f"{args['root']}/{args['experiment']}", "build.sh")

    build_dir = f"{args['root']}/{args['experiment']}"
    cmd_remote = f"bash -l {build_dir}/build.sh >{build_dir}/build.log 2>&1"
    cmd  = f'ssh hamilton -t "{cmd_remote}" '
    print(cmd)

    # Use run and wait to return - can't run multiple builds at the same time
    # as they all use the same build dirs
    return subprocess.run(cmd, shell=True).returncode

def generate_submit_script(args):

    with open("templates/sbatch-submit.sh") as f:
        submit = f.read()

    submit = submit.replace("<ROOT>",       args["root"])
    submit = submit.replace("<EXPERIMENT>", args["experiment"])
    submit = submit.replace("<EXE>",        args["executable"])
    submit = submit.replace("<CORES>",      args["cores"])
    submit = submit.replace("<USER>",       args["user"])
    submit = submit.replace("<LIB>",        args["lib"])
    submit = submit.replace("<PARTITION>",  args["partition"])
    submit = submit.replace("<TIME>",       args["time"])
    
    with open("submit.sh", "w") as f:
        f.write(submit)
    
    scp(args['user'], f"{args['root']}/{args['experiment']}", "submit.sh")

def submit_experiment(args):

    build_dir = f"{args['root']}/{args['experiment']}"
    cmd_remote = f"sbatch {build_dir}/submit.sh"
    cmd  = f'ssh hamilton -t "{cmd_remote}" '
    print(cmd)

    proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(proc.stdout)

def scp(user, dir, file):
    cmd = f"scp {file} {user}@hamilton:{dir}"
    print(cmd)
    proc = subprocess.run(cmd, shell=True)
    if proc.returncode != 0:
        raise RuntimeError(f"failed to copy {file} to remote")
    else:
        print(f"> {file} copied to remote")
