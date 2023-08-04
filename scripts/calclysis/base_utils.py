import pdb

import os
import re
import shutil
import time
import datetime

from scipy.spatial import distance

# from calclysis.elementdata import ElementData
# element_data = ElementData()


# populationは全パターン(all)か名前の組み合わせの形式で渡される
# 後者の場合, まずは名前の組み合わせをディレクトリ名へ変換する必要がある
def get_pop_dirs(population, comb_label=[], total_X_num=0):
    if population == 'all':
        path = '..'
        files = os.listdir(path)
        dirs = [f for f in files if os.path.isdir(os.path.join(path, f))]
        pop_dirs = [d for d in dirs if 'X1' in d]
    else:
        # automodeler.duplicate_checker.py内のコードと被っているので統合できるなら統合したい
        pop_dirs = []
        for name_comb in population:
            X_num = 1
            dir_name = ''
            while X_num <= total_X_num:
                dir_name += 'X' + str(X_num) + '-' + name_comb[X_num - 1]
                if X_num < total_X_num:
                    dir_name += '_'

                X_num += 1

            other_names = name_comb[total_X_num:]
            other_labels = comb_label[total_X_num:]
            if other_names:
                for name, label in zip(other_names, other_labels):
                    name = str(name)
                    if 'solvent' in label.lower():
                        dir_name += '_Sol-' + name
                    if 'temperature' in label.lower():
                        dir_name += '_Temp-' + name

            pop_dirs.append(dir_name)

    return pop_dirs


def get_atom_xyz(log_content, line_num, atom_number):
    atom_xyz_l = []
    for i in range(atom_number):
        tmp_atom_xyz = log_content[line_num + (i + 1)].rstrip('\n')
        tmp_atom_xyz = re.split(r'\s+', tmp_atom_xyz)
        atom_xyz = [tmp_atom_xyz[0]] + [float(j) for j in tmp_atom_xyz[1:]]
        atom_xyz_l.append(atom_xyz)

    return atom_xyz_l


def write_atom_xyz(c_calc_path, file_name, title_l, atom_xyz_l):
    file_name = file_name.split('.xyz')[0]
    xyz_file = open(c_calc_path + file_name + '.xyz', 'w')
    for title, atom_xyz in zip(title_l, atom_xyz_l):
        xyz_file.write(title)
        xyz_file.write('\n')
        for each_atom_xyz in atom_xyz:
            atom = each_atom_xyz[0].ljust(12)
            xyz = each_atom_xyz[1:]
            xyz = ['{:.1000f}'.format(float(k))[:14] for k in xyz]
            space = ' ' * 11
            xyz_file.write(atom + space.join(xyz))
            xyz_file.write('\n') 

        xyz_file.write('\n')         

    xyz_file.close()


class CheckBondCondition:
    def run(self, state, atom_xyz):
        # 2021-06-28追記
        if atom_xyz == []:
            return False

        rct_cond_l, ts_cond_l, prd_cond_l = self.get_bond_condition()
        if state == 'rct':
            cond_l = rct_cond_l
        if state == 'ts':
            cond_l = ts_cond_l
        if state == 'prd':
            cond_l = prd_cond_l

        isOK = self.check_condition(atom_xyz, cond_l)
        return isOK

    def get_bond_condition(self):
        bond_cond_file = open('bond_condition.com', 'r')
        bond_cond_content = bond_cond_file.readlines()
        bond_cond_file_len = len(bond_cond_content)
        bond_cond_file.close()

        rct_cond_l, ts_cond_l, prd_cond_l = [], [], []

        for line_num in range(bond_cond_file_len):
            com_line = bond_cond_content[line_num].rstrip('\n')
            com_line = com_line.lower()
            if 'rct bond condition' in com_line:
                rct_cond_l = self.read_input(bond_cond_content, line_num, rct_cond_l)
            if 'ts bond condition' in com_line:
                ts_cond_l = self.read_input(bond_cond_content, line_num, ts_cond_l)
            if 'prd bond condition' in com_line:
                prd_cond_l = self.read_input(bond_cond_content, line_num, prd_cond_l)

        # 仮にbond_condition.comにPRD bond conditionなどが指定されていない場合
        # そのcond_lは[[]]になるようにする
        if rct_cond_l == []:
            rct_cond_l.append([])
        if ts_cond_l == []:
            ts_cond_l.append([])
        if prd_cond_l == []:
            prd_cond_l.append([])

        return rct_cond_l, ts_cond_l, prd_cond_l

    def read_input(self, content, line_num, cond_l):
        row = 1
        each_cond = []
        while 'END' not in content[line_num + row]:
            new_com_line = content[line_num + row].rstrip('\n')
            if 'or' in new_com_line:
                cond_l.append(each_cond)
                each_cond = []
            else:
                condition = re.split(r'\s+', new_com_line)
                each_cond.append(condition)

            row += 1

        cond_l.append(each_cond)

        return cond_l

    # cond_lは最低でも[[]]なので、何もbond conditionをしていない場合は常にTrueが返る
    def check_condition(self, atom_xyz, cond_l):
        isOK = False
        for each_cond_l in cond_l:
            bond_cnt = 0
            check_bond_num = len(each_cond_l)
            for each_cond in each_cond_l:
                atom_i_num = int(each_cond[0]) - 1
                atom_j_num = int(each_cond[1]) - 1

                atom_i_atom_xyz = atom_xyz[atom_i_num]
                atom_j_atom_xyz = atom_xyz[atom_j_num]

                atom_i_atom = atom_i_atom_xyz[0]
                atom_j_atom = atom_j_atom_xyz[0]

                # covalent_radius = element_data.CovalentRadius[atom_i_atom] + \
                #                   element_data.CovalentRadius[atom_j_atom]
                # magnification = float(each_cond[3])
                # bond_len_thresh = covalent_radius * magnification

                bond_len_thresh = float(each_cond[3])

                atom_i_xyz = atom_i_atom_xyz[1:]
                atom_j_xyz = atom_j_atom_xyz[1:]

                bond_len = distance.euclidean(atom_i_xyz, atom_j_xyz)

                sign = each_cond[2]
                if sign == '<=' and bond_len <= bond_len_thresh:
                    bond_cnt += 1
                if sign == '>=' and bond_len >= bond_len_thresh:
                    bond_cnt += 1
                if sign == '<' and bond_len < bond_len_thresh:
                    bond_cnt += 1
                if sign == '>' and bond_len > bond_len_thresh:
                    bond_cnt += 1

            isOK = bool(bond_cnt == check_bond_num)
            if isOK:
                break

        return isOK


import subprocess
import calclysis.gen_shell
class SubmittJob:
    def __init__(self, machine='karura', node=None, pararrel=1, program_path=None):
        # self.machine = machine
        self.machine = machine.lower()
        self.node = node
        self.pararrel = pararrel
        self.program_path = program_path

    # インスタンス変数化してしまう
    def submit(self, calc_path, input_name, input_path, gauinput=False):
        self.calc_path = calc_path
        self.input_name = input_name
        self.input_path = input_path
        self.gauinput = gauinput

        shell_type = self.define_shell()
        self.shell_path = self.input_path + shell_type

        # resubmitの場合はシェルを作り直さない
        # オリジナルの並列数が維持される
        if not os.path.exists(self.shell_path):
            self.make_shell()

        # Gaussian以外にlinkしているなら必要なファイルを用意する
        link_name = self.get_link()
        if link_name != None:
            self.prepare_link_file(link_name)

        self.submit_job()

    def define_shell(self):
        if self.machine == 'kudpc':
            shell_type = '.csh'
        if self.machine == 'ims':
            shell_type = '.tcsh'
        if self.machine == 'karura':
            shell_type = '.sh'
        return shell_type

    def make_shell(self):
        if self.machine == 'kudpc':
            calclysis.gen_shell.shell_kudpc(self.calc_path, self.input_name,
                                            self.input_path, self.shell_path,
                                            self.pararrel, self.gauinput)
        if self.machine == 'ims':
            calclysis.gen_shell.shell_ims(self.calc_path, self.input_name,
                                          self.input_path, self.shell_path,
                                          self.pararrel, self.gauinput)
        if self.machine == 'karura':
            calclysis.gen_shell.shell_karura(self.calc_path, self.input_name,
                                             self.input_path, self.shell_path,
                                             self.pararrel, self.gauinput)

    def get_link(self):
        com_file = open(self.input_path + '.com', 'r')
        com_file_content = com_file.readlines()
        com_file.close()

        link_name = None
        for line in com_file_content:
            tmp_line = line.rstrip('\n')
            if '%link' in line:
                link_name = tmp_line.split('=')[-1]

        return link_name

    # Orcaを使うなら事前にORCA.inpというファイルをインプットファイルのディレクトリに置いておく
    def prepare_link_file(self, link_name):
        if link_name.lower() == 'orca':
            if os.path.exists(self.program_path + 'ORCA.inp'):
                shutil.copy(self.program_path + 'ORCA.inp', self.input_path + '.inp')
            else:
                shutil.copy(self.program_path + 'orca.inp', self.input_path + '.inp')

    def submit_job(self):
        if self.machine == 'kudpc':
            self.job_kudpc()
        if self.machine == 'ims':
            self.job_ims()
        if self.machine == 'karura':
            self.job_karura()

        dt_now = datetime.datetime.now()
        sub_log = open(self.calc_path + 'Submitted.log', 'w')
        sub_log.write('Submitted on ' + dt_now.strftime('%Y-%m-%d %H:%M:%S'))
        sub_log.close()

    def job_kudpc(self):
        subprocess.run(['qsub', self.shell_path])

    def job_ims(self):
        return
        subprocess.run(['jsub', '-q', 'PN', self.shell_path])

    def job_karura(self):
        proc_num, _ = calclysis.gen_shell.get_info(self.input_path)
        core_num = int(proc_num) * int(self.pararrel)
        core_num = str(core_num)

        if self.node is None or self.node == False:
            # node = False, Noneのときは全ノード指定
            self.node = 'ka04 ka05 ka06 ka07 ka08 ka09 ka10 ka11 ka12 ka13 ka14 ka15 ka16 ka17 ka18 ka19 ka20'

        subprocess.run(['bsub', '-n', core_num, '-q', 'normal',
                        '-m', self.node, '-R', 'span[hosts=1]', self.shell_path])

        # time.sleep(3)
