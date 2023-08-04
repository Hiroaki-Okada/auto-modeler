import pdb

import os
import re
import sys
import time

from automodeler.input_reader import ReadInput
from calclysis.base_utils import SubmittJob


class MinInputGenerator(ReadInput):
    def __init__(self, input_name, comb_label):
        super(MinInputGenerator, self).__init__(input_name)
        self.comb_label = comb_label

        self.calc_name = 'MIN'
        if self.option_dict['calc_name']:
            self.calc_name = self.option_dict['calc_name']

    def run(self, dir_name, name_comb, opt_atom_xyz):
        # program_path = os.getcwd() + '/'
        # ground_path = program_path + '../'

        dir_path = ReadInput.ground_path + dir_name + '/'

        # ある組み合わせのディレクトリが存在したとしてもRCT,PRD,MINなどで判別が必要
        # RCTなどのディレクトリが存在しているかどうかはmodel_generator.pyで調査済み
        if os.path.isdir(dir_path) == False:
            os.makedirs(ReadInput.ground_path + dir_name)

        # dir_path = ReadInput.ground_path + dir_name + '/'

        os.makedirs(dir_path + self.calc_name)
        self.calc_path = dir_path + self.calc_name + '/'

        self.input_name = dir_name + '_' + self.calc_name
        self.input_path = self.calc_path + self.input_name

        # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

        self.make_input(dir_name, name_comb, opt_atom_xyz)

        if self.option_dict['submit']:
            self.submit()

    def read_input(self):
        if os.path.exists(self.calc_name + '.com'):
            min_read = open(self.calc_name + '.com', 'r')
        else:
            try:
                raise FileExistsError('No input file!')
            except ValueError as e:
                traceback.print_exc()
                sys.exit(0)

        min_read_content = min_read.readlines()
        min_read.close()

        return min_read_content

    def make_input(self, dir_name, name_comb, opt_atom_xyz, scrf_type='SMD'):
        min_read_content = self.read_input()
        other_label_name_dict = self.get_other(name_comb)

        isAlreadyRead = False
        self.min_input = open(self.calc_path + self.input_name + '.com', 'w')
        for i in min_read_content:
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
            elif 'solvent' in other_label_name_dict and '#' in i:
                line = i.rstrip('\n')
                sol_name = other_label_name_dict['solvent']
                self.min_input.write(line + ' SCRF=(' + scrf_type + ', Solvent=' + sol_name + ')\n')
                # self.min_input.write(i)
            else:
                self.min_input.write(i)

        if 'temperature' in other_label_name_dict and isAlreadyRead:
            self.min_input.write('Temperature=' + other_label_name_dict['temperature'])

        self.min_input.close()

    # 2022-07-08 : 追加
    def get_other(self, name_comb):
        other_names = name_comb[self.total_X_num:]
        other_labels = self.comb_label[self.total_X_num:]

        other_dict = {}
        if other_names:
            for name, label in zip(other_names, other_labels):
                name = str(name)
                other_dict[label] = name

        return other_dict

    def write_atom_xyz(self, min_atom_xyz):
        for atom_xyz in min_atom_xyz:
            atom = atom_xyz[0].ljust(12)
            xyz = atom_xyz[1:]
            xyz = ['{:.1000f}'.format(float(k))[:14] for k in xyz]
            space = ' ' * 11
            self.min_input.write(atom + space.join(xyz))
            self.min_input.write('\n')

    def submit(self, machine='karura', node=None, pararrel=1):
        if self.option_dict['machine']:
            machine = self.option_dict['machine']
        if self.option_dict['node']:
            node = self.option_dict['node']
        if self.option_dict['pararrel']:
            pararrel = self.option_dict['pararrel']

        program_path = os.getcwd() + '/'

        submit_job = SubmittJob(machine=machine, node=node,
                                pararrel=pararrel, program_path=program_path)

        submit_job.submitt(self.calc_path, self.input_name, self.input_path)
