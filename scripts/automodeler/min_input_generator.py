import pdb

import os
import re
import sys
import time
import traceback

from automodeler.input_reader import ReadInput
from calclysis.base_utils import SubmitJob


class MinInputGenerator(ReadInput):
    def __init__(self, input_name, comb_label):
        super(MinInputGenerator, self).__init__(input_name)
        self.comb_label = comb_label

        self.calc_name = 'MIN'
        if self.option_dict['calc_name']:
            self.calc_name = self.option_dict['calc_name']

    def run(self, dir_name, name_comb, opt_atom_xyz):
        dir_path = os.path.join(ReadInput.ground_path, dir_name)

        # ある組み合わせのディレクトリが存在したとしても RCT, PRD, MIN などで判別が必要
        # RCT などのディレクトリが存在しているかどうかは model_generator.py で調査済み
        if os.path.isdir(dir_path) == False:
            os.makedirs(dir_path)

        self.calc_path = os.path.join(dir_path, self.calc_name)
        os.makedirs(self.calc_path)

        self.input_name = '{}_{}'.format(dir_name, self.calc_name)
        self.input_path = os.path.join(self.calc_path, self.input_name)

        self.make_input(dir_name, name_comb, opt_atom_xyz)

        if self.option_dict['submit']:
            self.submit()

    def make_input(self, dir_name, name_comb, opt_atom_xyz, scrf_type='SMD'):
        com_file_content = self.read_input()
        others_label_name_dict = self.get_others(name_comb)

        isAlreadyRead = False
        self.min_input = open(self.input_path + '.com', 'w')
        for i in com_file_content:
            if 'Options' in i:
                isAlreadyRead = True
                if self.option_dict['frozen']:
                    self.write_atom_xyz(opt_atom_xyz)
                    self.min_input.write('FrozenAtoms\n')
                    self.write_atom_xyz(self.model_not_X_atom_xyz)
                else:
                    self.write_atom_xyz(self.model_not_X_atom_xyz)
                    self.write_atom_xyz(opt_atom_xyz)

                self.min_input.write(i)

            # 2021-08-17 : 条件分岐追加
            elif i == '\n' and isAlreadyRead:
                break
            elif 'Remake' in i:
                break
            elif 'solvent' in others_label_name_dict and '#' in i:
                line = i.rstrip('\n')
                sol_name = others_label_name_dict['solvent']
                self.min_input.write('{} SCRF=({}, Solvent={})\n'.format(line, scrf_type, sol_name))
            else:
                self.min_input.write(i)

        if 'temperature' in others_label_name_dict and isAlreadyRead:
            self.min_input.write('Temperature={}'.format(others_label_name_dict['temperature']))

        self.min_input.close()

    def read_input(self):
        com_name = self.calc_name + '.com'
        if os.path.exists(com_name):
            com_file = open(com_name, 'r')
        else:
            try:
                raise FileExistsError('No input file for {} calculation!'.format(self.calc_name))
            except FileExistsError as e:
                traceback.print_exc()
                sys.exit(0)

        com_file_content = com_file.readlines()
        com_file.close()

        return com_file_content

    # 2022-07-08 : 追加
    def get_others(self, name_comb):
        others_names = name_comb[self.total_X_num:]
        others_labels = self.comb_label[self.total_X_num:]

        others_dict = {}
        if others_names:
            for name, label in zip(others_names, others_labels):
                name = str(name)
                others_dict[label] = name

        return others_dict

    def write_atom_xyz(self, min_atom_xyz):
        for atom_xyz in min_atom_xyz:
            atom = atom_xyz[0].ljust(12)
            xyz = atom_xyz[1:]
            xyz = ['{:.1000f}'.format(float(k))[:14] for k in xyz]
            space = ' ' * 11
            self.min_input.write(atom + space.join(xyz))
            self.min_input.write('\n')

    def submit(self, machine='karura', node=None, parallel=1):
        if self.option_dict['machine']:
            machine = self.option_dict['machine']
        if self.option_dict['node']:
            node = self.option_dict['node']
        if self.option_dict['parallel']:
            parallel = self.option_dict['parallel']

        program_path = os.getcwd()

        submit_job = SubmitJob(machine=machine, node=node,
                               parallel=parallel, program_path=program_path)

        submit_job.submit(self.calc_path, self.input_path, self.input_name)