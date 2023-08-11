import pdb

import os
import re
import sys
import subprocess


def get_info(input_path):
    com_file = open(input_path + '.com', 'r')
    com_file_content = com_file.readlines()
    com_file.close()

    proc_num = '1'
    infile_name = None
    for line in com_file_content:
        tmp_line = line.rstrip('\n')
        if '%infile' in tmp_line.lower():
            infile_name = tmp_line.split('=')[-1]
        if 'proc' in tmp_line.lower():
            proc_num = re.search(r'\d+', tmp_line).group()

    return proc_num, infile_name


def get_grrm_root():
    user_home = os.environ.get('HOME')
    grrm_root_path = os.path.join(user_home, 'GRRM/grrm.root')

    if not os.path.exists(grrm_root_path):
        print('grrm.root doesn\'t exists in {}'.format(grrm_root_path))
        sys.exit(0)

    grrm_root_file = open(grrm_root_path, 'r')
    grrm_root = grrm_root_file.readline()
    grrm_root_file.close()

    return grrm_root


def shell_karura(calc_path, input_name, input_path, shell_path, grrm_parallel_num, gauinput):
    proc_num, infile_name = get_info(input_path)
    memory = str(int(proc_num) * 3)

    user_name = os.environ.get('USER')
    grrm_root = get_grrm_root()

    sh_file = open(shell_path, 'w')

    sh_file.write('#!/bin/csh\n\n')

    sh_file.write('set DATA=' + calc_path + '\n')
    sh_file.write('set WORK=/scr/' + user_name + '.' + input_name + '.$$\n')
    sh_file.write('set GRRM=' + grrm_root + '\n')

    sh_file.write('setenv subgrr ${GRRM}/GRRM.out\n')
    sh_file.write('setenv submpi mpirun\n')
    sh_file.write('setenv g16root /usr/local/gaussian16b01\n')
    sh_file.write('setenv GAUSS_SCRDIR /scr\n')
    sh_file.write('setenv OMP_NUM_THREADS 1\n')
    sh_file.write('source $g16root/g16/bsd/g16.login\n')
    sh_file.write('setenv subgau g16\n')
    sh_file.write('setenv subchk formchk\n')
    sh_file.write('setenv subuchk unfchk\n')
    sh_file.write('setenv submol "molpro -W${WORK} -d${WORK}"\n')
    sh_file.write('setenv subsiesta siesta\n')
    sh_file.write('setenv siestascr ${WORK}\n')
    sh_file.write('setenv TURBODIR /usr/local/TURBOMOLE7.0/TURBOMOLE\n')
    sh_file.write('set path = ( $TURBODIR/scripts $path)\n')

    if int(proc_num) != 1:
        sh_file.write('setenv PARA_ARCH SMP\n')

    sh_file.write('set path = ($TURBODIR/bin/`sysname` $path)\n')
    sh_file.write('setenv subgms /usr/local/gamess/rungms\n')
    sh_file.write('setenv gmstmp ~/scr\n')
    sh_file.write('setenv gmsscr1 ${WORK}\n')
    sh_file.write('setenv gmsscr2 /home/' + user_name + '/scr\n')
    sh_file.write('if (! -d /scr/' + user_name + ' ) mkdir -m 700 /scr/' + user_name + '\n')
    sh_file.write('setenv subqchem /usr/local/qchem-4.1.2/exe/qcprog.exe\n')
    sh_file.write('setenv qchemtmp ${WORK}\n')
    sh_file.write('setenv QC /usr/local/qchem-4.1.2\n')
    sh_file.write('setenv subdalton /home/grrm_admin/buchi/dalton/buchi_dalton/dalton\n')
    sh_file.write('setenv daltontmp ${WORK}\n')
    sh_file.write('setenv submndo /usr/local/mndo99/mndo99_20161021_intel64_ifort-13.1.3.192_mkl-11.1.4.211\n')
    sh_file.write('setenv subvasp /usr/local/VASP-5.3.3-22May2013/bin/vasp\n')
    sh_file.write('setenv subdftb_plus /usr/local/dftb_plus/bin/dftb+ \n')
    sh_file.write('alias cp \'cp -pf\'\n\n')

    sh_file.write('setenv suborca /home/SIESTA/hiro/orca_4_2_1_linux_x86-64_openmpi314/orca\n\n')

    sh_file.write('if ( -d ${WORK} ) rm -rf ${WORK}\n')
    sh_file.write('mkdir -m 700 ${WORK}\n\n')

    sh_file.write('mv ${DATA}/' + input_name + '.log ${WORK}\n')
    sh_file.write('mv ${DATA}/' + input_name + '_* ${WORK}\n')
    sh_file.write('cp ${DATA}/' + input_name + '.* ${WORK}\n')
    sh_file.write('cp ${DATA}/*.inp ${WORK}\n')
    sh_file.write('cp ${DATA}/*.psf ${WORK}\n')
    sh_file.write('cp ${DATA}/*.hsd ${WORK}\n')
    sh_file.write('cp ${DATA}/' + input_name + '/* ${WORK}\n\n')

    if infile_name != None:
        sh_file.write('cp ${DATA}/' + infile_name + '.log ${WORK}\n')
        sh_file.write('cp ${DATA}/' + infile_name + '_EQ* ${WORK}\n')
        sh_file.write('cp ${DATA}/' + infile_name + '_TS* ${WORK}\n')
        sh_file.write('cp ${DATA}/' + infile_name + '_DC* ${WORK}\n')
        sh_file.write('cp ${DATA}/' + infile_name + '_PT* ${WORK}\n')
        sh_file.write('cp ${DATA}/' + infile_name + '_*DONE.rrm ${WORK}\n')
        sh_file.write('cp ${DATA}/' + infile_name + '_*MO.rrm* ${WORK}\n')

    sh_file.write('cd ${WORK}\n')

    if gauinput == False:
        sh_file.write('${GRRM}/GRRMp ' + input_name + ' -p' + str(grrm_parallel_num) + ' -s172800\n\n')
    # 2021-08-27 : 要追記
    else:
        i = 0

    sh_file.write('cp ${WORK}/' + input_name + '.* ${DATA}\n')
    sh_file.write('cp ${WORK}/' + input_name + '_* ${DATA}\n\n')

    sh_file.write('cd ${DATA}\n')
    sh_file.write('rm -rf ${WORK}\n\n\n\n')

    sh_file.close()

    subprocess.call(['chmod', '750', shell_path])


def shell_ims(calc_path, input_name, input_path, shell_path, grrm_parallel_num, gauinput, walltime='144'):
    proc_num, infile_name = get_info(input_path)
    request_core_num = int(proc_num) * int(grrm_parallel_num)
    if request_core_num <= 64:
        node_num = '1'
        ncpus = ompthreads = str(request_core_num)
    else:
        node_num = str((request_core_num + 64 - 1) // 64)
        ncpus = ompthreads = '64'

    grrm_root = get_grrm_root()

    tcsh_file = open(shell_path, 'w')

    tcsh_file.write('#!/bin/tcsh -f\n')
    tcsh_file.write('#PBS -l select=' + node_num + ':ncpus=' + ncpus + ':mpiprocs=1:ompthreads=' + ompthreads + '\n')
    tcsh_file.write('#PBS -l walltime=' + walltime  + ':0:0\n\n')

    tcsh_file.write('set input=' + input_name + '\n')
    tcsh_file.write('set DATA=' + calc_path + '\n\n')

    tcsh_file.write('set GRRM=' + grrm_root + '\n')
    tcsh_file.write('set WORK=/gwork/users/${USER}/' + input_name + '.$$\n\n\n')

    tcsh_file.write('# # # # # Gaussian16 at IMS # # # # #\n')
    tcsh_file.write('set g16=16c01\n')
    tcsh_file.write('setenv g16root /apl/gaussian/${g16}\n')
    tcsh_file.write('source ${g16root}/g16/bsd/g16.login\n')
    tcsh_file.write('setenv GAUSS_SCRDIR ${WORK}\n')
    tcsh_file.write('setenv subgau g16\n')
    tcsh_file.write('setenv subchk formchk\n\n\n')

    tcsh_file.write('# # # # # SIESTA VER.4.1.5 at IMS # # # # #\n')
    tcsh_file.write('setenv siestascr ${WORK}\n')
    tcsh_file.write('setenv subsiesta /apl/siesta/4.1.5-mpi/bin/siesta\n\n\n')

    tcsh_file.write('# # # # # TURBOMOLE VER.7.6 at IMS # # # # #\n')
    tcsh_file.write('setenv TURBODIR "/apl/turbomole/7.6"\n')
    tcsh_file.write('setenv PARA_ARCH SMP\n')
    tcsh_file.write('setenv TM_PAR_FORK on\n')
    tcsh_file.write('source ${TURBODIR}/Config_turbo_env.csh\n')
    tcsh_file.write('set path = ($TURBODIR/scripts $path)\n')
    tcsh_file.write('set path = ($TURBODIR/bin/`sysname` $path)\n\n\n')

    tcsh_file.write('# # # # # Orca4.2 at IMS # # # # #\n')
    tcsh_file.write('setenv suborca /home/users/bqf/my_software/Orca4.2/orca_4_2_1_linux_x86-64_openmpi314/orca\n\n\n')

    tcsh_file.write('setenv LANG C\n')
    tcsh_file.write('setenv subgrr ./GRRM.out\n\n')

    tcsh_file.write('if ( -d ${WORK} ) rm -rf ${WORK}\n')
    tcsh_file.write('mkdir  ${WORK}\n\n')

    tcsh_file.write('# TURBOMOLE settings start\n')
    tcsh_file.write('cp     ${DATA}/mos       ${WORK}\n')
    tcsh_file.write('cp     ${DATA}/basis     ${WORK}\n')
    tcsh_file.write('cp     ${DATA}/control   ${WORK}\n')
    tcsh_file.write('cp     ${DATA}/coord     ${WORK}\n')
    tcsh_file.write('cp     ${DATA}/alpha     ${WORK}\n')
    tcsh_file.write('cp     ${DATA}/beta      ${WORK}\n')
    tcsh_file.write('cp     ${DATA}/auxbasis  ${WORK}\n')
    tcsh_file.write('cp     ${DATA}/${input} ${WORK}\n\n')

    tcsh_file.write('cp     ${DATA}/${input}.* ${WORK}\n')
    tcsh_file.write('mv     ${DATA}/${input}_* ${WORK}\n')

    if infile_name is not None:
         tcsh_file.write('cp -r  ${DATA}/' + infile_name + '* ${WORK}\n')

    tcsh_file.write('cp     ${GRRM}/GRRMp    ${WORK}\n')
    tcsh_file.write('cp     ${GRRM}/GRRM.out ${WORK}\n\n')

    tcsh_file.write('cd     ${WORK}\n')

    if gauinput == False:
        tcsh_file.write('./GRRMp ' + input_name + ' -p' + str(grrm_parallel_num)  + ' -h' + str(int(walltime) - 2)  + '\n\n')
    else:
        tcsh_file.write('/apl/gaussian/16c01/g16/g16 ' + input_name + '.com\n\n')

    tcsh_file.write('cp -f  ${WORK}/${input}.* ${DATA}\n')
    tcsh_file.write('cp -f  ${WORK}/${input}_* ${DATA}\n\n')

    tcsh_file.write('cd     ${DATA}\n')
    tcsh_file.write('rm -rf ${WORK}\n\n\n')

    tcsh_file.close()

    subprocess.call(['chmod', '750', shell_path])


def shell_kudpc(calc_path, input_name, input_path, shell_path, grrm_parallel_num, gauinput):
    proc_num, infile_name = get_info(input_path)
    memory = str(int(proc_num) * 3)

    # # # # # # # # # # # # # # # # # # # #
    user_home = os.environ.get('HOME') + '/'
    user_name = os.environ.get('USER')

    que_name = 'gr10297b'
    group_name = 'gr10297'
    # # # # # # # # # # # # # # # # # # # #

    grrm_root_file = open(user_home + 'GRRM/grrm.root', 'r')
    grrm_root = grrm_root_file.readline()
    grrm_root_file.close()

    csh_file = open(shell_path, 'w')
    csh_file.write('#!/bin/csh -f\n')
    csh_file.write('#============ PBS Options ============\n')
    csh_file.write('#QSUB -q ' + que_name + '\n')
    csh_file.write('#QSUB -ug ' + group_name + '\n')
    csh_file.write('#QSUB -W 72:0\n')
    csh_file.write('#QSUB -A p=1:t=' + proc_num + ':c=' + proc_num + ':m=' + memory +'G\n')
    csh_file.write('#QSUB -r n\n')
    csh_file.write('#=====================================\n\n')

    '''
    QSUB_WORKDIR is the current directory where the job was submitted.
    When you specify a csh to qsub from a directory (dir = B) instead of the directory
    where the csh file is located (dir = A) by absolute path, QSUB_WORKDIR will contain B.
    In this case, the HOSTCheck file are created in B.
    But the com file exists in A. Therefore, the calculation will not proceed properly.
    To work around this problem, you can specify the DATA path in QSUB_WORKDIR.
    '''
    # csh_file.write('cd ${QSUB_WORKDIR}\n')

    csh_file.write('set DATA=' + calc_path + '\n')
    csh_file.write('cd ${DATA}\n\n')

    csh_file.write('pwd | grep \'^/LARGE\' >& /dev/null\n')
    csh_file.write('if ( $status == 0 ) then\n')
    csh_file.write('  set WORK=${DATA}\n')
    csh_file.write('else\n')
    csh_file.write('  set WORK=/LARGE0/' + group_name + '/' + user_name + '/' + input_name + '.$$\n')
    csh_file.write('  if ( -d ${WORK} ) rm -rf ${WORK}\n')
    csh_file.write('  mkdir -m 700 -p ${WORK}\n')
    csh_file.write('endif\n')
    csh_file.write('setenv SCR ${TMPDIR}\n')
    csh_file.write('set GRRM=' + grrm_root + '\n')
    csh_file.write('setenv subgrr ${GRRM}/GRRM.out\n\n')

    csh_file.write('source /opt/Modules/3.2.6/init/csh\n')
    csh_file.write('module load intel/17.0.1.132\n')
    csh_file.write('module load impi/2017.1\n')
    csh_file.write('setenv submpi mpirun\n')
    csh_file.write('module load gaussian16/b01\n')
    csh_file.write('setenv subgau g16\n')
    csh_file.write('setenv subchk formchk\n')
    csh_file.write('setenv GAUSS_SCRDIR ${SCR}\n')
    csh_file.write('module load gamess/2016R1_intel-17.0-impi-2017.1\n')
    csh_file.write('setenv subgms rungms\n')
    csh_file.write('setenv gmstmp ${SCR}\n')
    csh_file.write('setenv gmsscr1 ${SCR}\n')
    csh_file.write('setenv gmsscr2 ${WORK}\n')
    csh_file.write('setenv subsiesta "/LARGE0/gr10297/siesta-4.0.2_intel-17.0-impi-2017.1/bin/siesta"\n')
    csh_file.write('setenv subdftb_plus "/LARGE0/gr10297/dftb_plus/bin/dftb+"\n')
    csh_file.write('setenv TURBODIR "/LARGE0/gr10297/TURBOMOLE_73/TURBOMOLE"\n')
    csh_file.write('setenv PARA_ARCH SMP\n')
    csh_file.write('setenv TM_PAR_FORK on\n')
    csh_file.write('set path = ($TURBODIR/scripts $path)\n')
    csh_file.write('set path = ($TURBODIR/bin/`sysname` $path)\n\n')

    csh_file.write('alias cp \'cp -pf\'\n\n')

    csh_file.write('if ( ${WORK} != ${DATA} ) then\n')
    csh_file.write('  if ( -e ${DATA}/' + input_name + '.log ) mv ${DATA}/' + input_name + '.log ${WORK}/\n')
    csh_file.write('  ls ${DATA}/' + input_name + '_* >& /dev/null\n')
    csh_file.write('  if ( $status == 0 ) mv ${DATA}/' + input_name + '_* ${WORK}/\n')
    csh_file.write('  ls ${DATA}/' + input_name + '.* >& /dev/null\n')
    csh_file.write('  if ( $status == 0 ) cp ${DATA}/' + input_name + '.* ${WORK}/\n')
    csh_file.write('  ls ${DATA}/*.inp >& /dev/null\n')
    csh_file.write('  if ( $status == 0 ) cp ${DATA}/*.inp ${WORK}/\n')
    csh_file.write('  ls ${DATA}/*.psf >& /dev/null\n')
    csh_file.write('  if ( $status == 0 ) cp ${DATA}/*.psf ${WORK}/\n')
    csh_file.write('  if ( -d ${DATA}/' + input_name + ' ) cp ${DATA}/' + input_name + '/* ${WORK}/\n')

    if infile_name != None:
        csh_file.write('  cp ${DATA}/' + infile_name + '.log ${WORK}\n')
        csh_file.write('  ls ${DATA}/' + infile_name + '_EQ* >& /dev/null\n')
        csh_file.write('  if ( $status == 0 ) cp ${DATA}/' + infile_name + '_EQ* ${WORK}\n')
        csh_file.write('  ls ${DATA}/' + infile_name + '_TS*.log >& /dev/null\n')
        csh_file.write('  if ( $status == 0 ) cp ${DATA}/' + infile_name + '_TS*.log ${WORK}\n')
        csh_file.write('  ls ${DATA}/' + infile_name + '_DC*.log >& /dev/null\n')
        csh_file.write('  if ( $status == 0 ) cp ${DATA}/' + infile_name + '_DC*.log ${WORK}\n')
        csh_file.write('  ls ${DATA}/' + infile_name + '_PT*.log >& /dev/null\n')
        csh_file.write('  if ( $status == 0 ) cp ${DATA}/' + infile_name + '_PT*.log ${WORK}\n')
        csh_file.write('  ls ${DATA}' + infile_name + '_*DONE.rrm >& /dev/null\n')
        csh_file.write('  if ( $status == 0 ) cp ${DATA}/' + infile_name + '_*DONE.rrm ${WORK}\n')
        csh_file.write('  ls ${DATA}' + infile_name + '_*MO.rrm* >& /dev/null\n')
        csh_file.write('  if ( $status == 0 ) cp ${DATA}/' + infile_name + '_*MO.rrm* ${WORK}\n')

    csh_file.write('  cd ${WORK}\n')
    csh_file.write('endif\n\n')

    if gauinput == False:
        csh_file.write('${GRRM}/GRRMp ' + input_name + ' -p' + str(grrm_parallel_num) + ' -s252000\n\n')
    # 2021-08-27 : 要追記
    else:
        csh_file.write('g16 ' + input_name + '\n\n')

    csh_file.write('if ( ${WORK} != ${DATA} ) then\n')
    csh_file.write('  ls ${WORK}/' + input_name + '.* >& /dev/null\n')
    csh_file.write('  if ( $status == 0 ) cp ${WORK}/' + input_name + '.* ${DATA}/\n')
    csh_file.write('  ls ${WORK}/' + input_name + '_* >& /dev/null\n')
    csh_file.write('  if ( $status == 0 ) cp ${WORK}/' + input_name + '_* ${DATA}/\n')
    csh_file.write('  cd ${DATA}\n')
    csh_file.write('  rm -rf ${WORK}\n')
    csh_file.write('endif\n')
    csh_file.write('\n\n\n')
    csh_file.close()

    subprocess.run(['chmod', '750', shell_path])