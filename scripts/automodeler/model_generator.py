import pdb

import os

from automodeler.input_reader import ReadInput
from automodeler.duplicate_checker import DuplicateChecker
from automodeler.conformation_generator import ConformationGenerator
from automodeler.min_input_generator import MinInputGenerator


class ModelGenerator(ReadInput):
    # comb_label って何だっけ？
    def __init__(self, input_name, comb_label=[]):
        super(ModelGenerator, self).__init__(input_name)

        if comb_label == []:
            self.comb_label = ['X' for i in range(self.total_X_num)]
        else:
            self.comb_label = comb_label

        self.duplicate_checker = DuplicateChecker(input_name, comb_label=comb_label)
        self.conformation_generator = ConformationGenerator(input_name)
        self.min_input_generator = MinInputGenerator(input_name, comb_label=comb_label)

    def run(self, combination):
        '''combination の表現方法には3通りのパターンがある
        1. 数値のリスト    : combination = [1, 2, 3, 4, 5]
        2. 文字列のリスト1 : combination = ['1', '2', '3', '4', '5']
        3. 名前のリスト    : combination = ['NH2', 'OCH3', 'H', 'F', 'CN']
        3を基準として、1や2だった場合は名前のリスト(name_comb)に変換する'''
        try:
            combination = [int(i) for i in combination]
            name_comb = self.get_ini_name_comb(combination)
        except:
            name_comb = combination[:]

        # name_comb には other_components も含まれている可能性がある(ベイズと連動した場合)が, c_name_comb は X 要素のみ含まれている
        c_dir_name, c_name_comb, isDuplicate = self.check_duplicate(name_comb)

        # パスはクラス変数にアクセスして読む
        # dir_path = ReadInput.ground_path + c_dir_name + '/' + self.option_dict['calc_name']
        dir_path = os.path.join(ReadInput.ground_path, c_dir_name, self.option_dict['calc_name'])

        # 2021-08-05:条件分岐を変更
        # if not isDuplicate:
        if os.path.isdir(dir_path) == False:
            generated_coordinate = self.generate_cartesian_coordinate(c_name_comb)
            full_atom_xyz = self.model_not_X_atom_xyz + generated_coordinate
            # self.make_min_input(c_dir_name, c_name_comb, generated_coordinate)
            self.make_min_input(c_dir_name, name_comb, generated_coordinate)
        else:
            full_atom_xyz = []

        return c_dir_name, isDuplicate, full_atom_xyz

    def get_ini_name_comb(self, combination):
        name_comb = []
        for number in combination:
            name = self.num_cand_name_dict[number]
            name_comb.append(name)

        return name_comb

    def check_duplicate(self, name_comb, seen=set()):
        c_dir_name, c_name_comb, isDuplicate = self.duplicate_checker.run(name_comb, seen)
        return c_dir_name, c_name_comb, isDuplicate

    def generate_cartesian_coordinate(self, c_name_comb):
        generated_coordinate = self.conformation_generator.run(c_name_comb)
        return generated_coordinate

    def make_min_input(self, c_dir_name, c_name_comb, generated_coordinate):
        self.min_input_generator.run(c_dir_name, c_name_comb, generated_coordinate)
