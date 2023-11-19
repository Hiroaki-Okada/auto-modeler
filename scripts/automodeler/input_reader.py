import pdb

import os
import re
from collections import defaultdict


# インプットから読みこんだ情報は str 型なので, 事前に変換しておく
def convert_str(s):
    if s.lower() == 'true':
        return True
    elif s.lower() == 'false':
        return False
    elif s.lower() == 'none':
        return None
    else:
        return s


def read_options(option_dict, com_file_content, line_num):
    row = 0
    while 'end' not in com_file_content[line_num + (row + 1)].lower():
        option_line = com_file_content[line_num + (row + 1)].rstrip('\n')
        option_line = re.split(r'\s?=\s?', option_line)
        option_info = convert_str(option_line[-1])

        # str 型(デフォルトは MIN)
        if 'calc' in option_line:
            option_dict['calc_name'] = option_info
        # bool 値
        if 'frozen' in option_line:
            option_dict['frozen'] = option_info
        # bool 値
        if 'submit' in option_line:
            option_dict['submit'] = option_info
        # 文字列で指定(デフォルトは karura)
        if 'machine' in option_line:
            option_dict['machine'] = option_info
        # node は None でも False でも OK
        # いずれかを指定した場合は全ノードを対象に投入する
        if 'node' in option_line:
            option_dict['node'] = option_info
        # シェルスクリプトを作成する際に使用する(デフォルト値は 1)
        # 内部で str に変換されるので int でも str でも良い
        if 'parallel' in option_line:
            option_dict['parallel'] = option_info

        row += 1

    return option_dict


class ReadInput(object):
    ground_path = os.path.join(os.getcwd(), '..')

    def __init__(self, input_name):
        com_file = open(input_name + '.com', 'r')
        com_file_content = com_file.readlines()
        com_file_len = len(com_file_content)
        com_file.close()

        # bool() は False を返すので, False が初期値となる
        self.option_dict = defaultdict(bool)
        for line_num in range(com_file_len):
            if 'options' in com_file_content[line_num].lower():
                self.option_dict = read_options(self.option_dict, com_file_content, line_num)

            if com_file_content[line_num].lower() == 'model molecule\n':
                self.model_atom_xyz = []
                self.model_X_atom_xyz = []
                self.model_not_X_atom_xyz = []

                self.total_X_num = 0

                self.atom_mode_X_inx = []
                self.sub_mode_X_inx = []
                self.mol_mode_X_inx = []

                self.part_mode_X_inx_dict = {}
                self.part_root_atom_xyz_dict = {}
                self.root_list_of_each_X = []

                self.X_inx_perm_dict = {}

                self.ori_X_dir_inx_rel = []

                row = 0
                X_inx = 0
                while com_file_content[line_num + (row + 1)] != 'END\n':
                    com_line = com_file_content[line_num + (row + 1)].rstrip('\n')
                    com_line = re.split(r'\s+', com_line)

                    # perm : X の並びと, 実際の X の番号を対応付けるリスト
                    # 一番上の X を X2 にしたいならば, perm は 2 にする
                    # perm : X の並びと, 実際の X の番号を対応付けるリスト
                    # part : X のグループ番号。同じグループにある X は enum モードに従って重複判定がされうる
                    # root : X の結合元の原子（分子モードの場合どうなんだっけ)
                    # X_root : X の元々の並び (?) なんで追加したか思い出せない
                    atom_xyz = com_line[:4]
                    atom_xyz = [atom_xyz[0]] + [float(i) for i in atom_xyz[1:]]
                    perm = int(com_line[4])
                    part = int(com_line[5])
                    root = int(com_line[6])
                    X_root = int(com_line[7])
                    mode = com_line[8]
                    enum = com_line[9]

                    self.model_atom_xyz.append(atom_xyz)

                    if 'X' in atom_xyz[0]:
                        self.total_X_num += 1
                        self.model_X_atom_xyz.append(atom_xyz)
                        self.root_list_of_each_X.append(X_root)

                        self.X_inx_perm_dict[X_inx] = perm - 1

                        if root != 0:
                            self.part_root_atom_xyz_dict[root] = tuple(atom_xyz)

                        if mode == 'A':
                            self.atom_mode_X_inx.append(X_inx)
                        elif mode == 'S':
                            self.sub_mode_X_inx.append(X_inx)
                        elif mode == 'M':
                            self.mol_mode_X_inx.append(X_inx)

                        if part in self.part_mode_X_inx_dict:
                            self.part_mode_X_inx_dict[part][1].append(X_inx)
                        else:
                            self.part_mode_X_inx_dict[part] = [enum, [X_inx]]

                        X_inx += 1

                    else:
                        self.model_not_X_atom_xyz.append(atom_xyz)
                        if root != 0:
                            self.part_root_atom_xyz_dict[root] = tuple(atom_xyz)

                    row += 1

                for mode, X_inx_list in self.part_mode_X_inx_dict.values():
                    self.ori_X_dir_inx_rel += X_inx_list

        self.locus_cand_name_atom_xyz = [[] for i in range(self.total_X_num)]
        self.locus_cand_num_list = []

        self.cand_name_num_dict = {}
        self.num_cand_name_dict = {}

        self.total_patterns = 1

        sub_inx = -1
        line_num = 0
        cand_num = 0
        while line_num < com_file_len:
            if 'list' in com_file_content[line_num]:
                sub_inx += 1

                each_locus_cand_num_list = 0
                while com_file_content[line_num] != 'END\n':
                    each_locus_cand_num_list += 1
                    each_sub_atom_xyz = []
                    each_sub_name = com_file_content[line_num + 1].rstrip('\n')
                    each_sub_atom_num = com_file_content[line_num + 2].rstrip('\n')
                    each_sub_atom_num = int(each_sub_atom_num)

                    row = 2
                    for row in range(row, row + each_sub_atom_num):
                        temp_atom_xyz = com_file_content[line_num + (row + 1)].rstrip('\n')
                        atom_xyz = re.split(r'\s+', temp_atom_xyz)
                        atom_xyz = [atom_xyz[0]] + [float(i) for i in atom_xyz[1:]]
                        atom_xyz = tuple(atom_xyz)

                        each_sub_atom_xyz.append(atom_xyz)
                        row += 1

                    if each_sub_name not in self.cand_name_num_dict:
                        self.cand_name_num_dict[each_sub_name] = cand_num
                        self.num_cand_name_dict[cand_num] = each_sub_name
                        cand_num += 1

                    each_sub_atom_xyz = tuple(each_sub_atom_xyz)
                    self.locus_cand_name_atom_xyz[sub_inx].append((each_sub_name,
                                                                   each_sub_atom_xyz))
                    line_num += row + 1

                self.total_patterns *= each_locus_cand_num_list
                self.locus_cand_num_list.append(each_locus_cand_num_list)

            line_num += 1

        self.locus_cand_name_atom_xyz = \
        tuple([tuple(i) for i in self.locus_cand_name_atom_xyz])

        self.locus_name_num_dict_list = []
        self.locus_gene_list = []

        for X_num in range(self.total_X_num):
            locus_name_num_dict = {}
            locus_gene = []
            for cand_inx in range(self.locus_cand_num_list[X_num]):
                cand_name = self.locus_cand_name_atom_xyz[X_num][cand_inx][0]
                cand_num = self.cand_name_num_dict[cand_name]

                locus_name_num_dict[cand_num] = cand_name
                locus_gene.append(cand_num)

            self.locus_name_num_dict_list.append(locus_name_num_dict)
            self.locus_gene_list.append(locus_gene)
