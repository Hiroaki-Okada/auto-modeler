import pdb

import os

from automodeler.input_reader import ReadInput
from automodeler.duplicate_checker import DuplicateChecker
from automodeler.conf_designer import ConfDesigner
from automodeler.min_input_generator import MinInputGenerator


class ModelGenerator(ReadInput):
    def __init__(self, input_name, comb_label=[]):
        super(ModelGenerator, self).__init__(input_name)

        if comb_label == []:
            self.comb_label = ['X' for i in range(self.total_X_num)]
        else:
            self.comb_label = comb_label

        self.duplicate_checker = DuplicateChecker(input_name, comb_label=comb_label)
        self.conf_designer = ConfDesigner(input_name)
        self.min_input_generator = MinInputGenerator(input_name, comb_label=comb_label)

    def run(self, individual):
        # individualは3通りのパターンがある
        # 1. 数値のリスト: individual = [1, 2, 3, 4, 5]
        # 2. 文字列のリスト1 : individual = ['1', '2', '3', '4', '5']
        # 3. 文字列のリスト2 : individual = ['NH2', 'OCH3', 'H', 'F', 'CN']
        # 3を基準として1や2だった場合は名前のリストに変換することを考える
        # 基本的には名前のリストを渡すようにする
        try:
            individual = [int(i) for i in individual]
            name_comb = self.get_ini_name_comb(individual)
        except:
            name_comb = individual[:]

        # name_combにはother_componentsも含まれているが, c_name_combはXの要素のみ含まれている
        c_dir_name, c_name_comb, isDuplicate = self.duplicate_check(name_comb)

        # 2021-08-05:条件分岐を変更
        # パスはクラス変数にアクセスして読む
        dir_path = ReadInput.ground_path + c_dir_name + '/' + self.option_dict['calc_name']

        # if not isDuplicate:
        if os.path.isdir(dir_path) == False:
            designed_atom_xyz = self.build_model(c_name_comb)
            full_atom_xyz = self.model_not_X_atom_xyz + designed_atom_xyz
            # self.make_min_input(c_dir_name, c_name_comb, designed_atom_xyz)
            self.make_min_input(c_dir_name, name_comb, designed_atom_xyz)
        else:
            full_atom_xyz = []

        return c_dir_name, isDuplicate, full_atom_xyz

    def get_ini_name_comb(self, individual):
        name_comb = []
        for gene in individual:
            name = self.num_cand_name_dict[gene]
            name_comb.append(name)

        return name_comb

    def duplicate_check(self, name_comb, seen=set()):
        c_dir_name, c_name_comb, isDuplicate = self.duplicate_checker.run(name_comb, seen)
        return c_dir_name, c_name_comb, isDuplicate

    def build_model(self, c_name_comb):
        designed_atom_xyz = self.conf_designer.run(c_name_comb)
        return designed_atom_xyz

    def make_min_input(self, c_dir_name, c_name_comb, designed_atom_xyz):
        self.min_input_generator.run(c_dir_name, c_name_comb, designed_atom_xyz)
