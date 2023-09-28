import pdb

import os
import sys
sys.setrecursionlimit(10**9)

from automodeler.input_reader import ReadInput


class DuplicateChecker(ReadInput):
    def __init__(self, input_name, comb_label):
        super(DuplicateChecker, self).__init__(input_name)
        self.comb_label = comb_label

    # seen : ディレクトリを作成せずに組み合わせを列挙する時に使う
    def run(self, name_comb, seen=set()):
        self.name_comb = name_comb
        self.seen = seen

        '''name_comb には, X 以外にも other_components の情報が数値や HOE の形式で含まれることがある
        しかし, other_components の情報はインプットファイルである read.com には記載されていない
        従って, X 以外の要素はモデル分子作成に用いる name_enum_l に組み込まれない
        以上より, other_components の有無にかかわらず, automodeler の改良は不要である'''
        # 各パートに対して可能な組みあわせを列挙して保存する
        self.part_X_name_enum_l = self.get_name_enum(name_comb)

        self.dir_name_l = []
        self.name_comb_l = []
        self.isDuplicate_l = []

        # DFS による全探索で可能な組み合わせが全列挙され, その中で重複しているものがあるか判定する
        # 重複していない場合は model_generator で座標生成が実行される
        self.dfs_enumeration([])

        if any(self.isDuplicate_l):
            idx = self.isDuplicate_l.index(True)
            c_dir_name = self.dir_name_l[idx]
            c_name_comb = self.name_comb_l[idx]
            isDuplicate = True
        else:
            c_dir_name = self.dir_name_l[0]
            c_name_comb = self.name_comb_l[0]
            isDuplicate = False

        c_name_comb = tuple(c_name_comb)

        print('\nDuplication judge : {}'.format(isDuplicate))

        return c_dir_name, c_name_comb, isDuplicate

    def get_name_enum(self, name_comb):
        """
        アルゴリズムに再考の余地あり
        Pモード : 順列(permitation)列挙. 重複を考慮せず, 全組み合わせをそのまま生成
        Bモード : 数珠順列(bead)列挙. 同一グループの候補名をソートすれば一意に 1 つの組み合わせに限定できる
        Cモード : 組み合わせ(combination)列挙. 光学異性体を区別したい時に使う. 3 つの組み合わせをローテンションさせ, 存在するか確認する
        """
        part_X_name_enum_l = []
        for mode, X_idx in self.part_mode_X_inx_dict.values():
            name_l = []
            for idx in X_idx:
                name_l.append(name_comb[idx])

            each_part_X_name_enum_l = []
            if mode == 'P':
                each_part_X_name_enum_l.append(name_l)
            elif mode == 'B':
                each_part_X_name_enum_l.append(sorted(name_l))
            elif mode == 'C':
                for i in range(len(name_l)):
                    temp_name_l = name_l[i:] + name_l[:i]
                    if temp_name_l not in each_part_X_name_enum_l:
                        each_part_X_name_enum_l.append(temp_name_l)

            part_X_name_enum_l.append(each_part_X_name_enum_l)

        return part_X_name_enum_l

    def dfs_enumeration(self, temp_name_enum):
        if len(temp_name_enum) == len(self.part_X_name_enum_l):
            name_enum_l = sum(temp_name_enum, [])

            new_name_comb = [''] * self.total_X_num
            for name, dir_idx in zip(name_enum_l, self.ori_X_dir_inx_rel):
                new_name_comb[dir_idx] = name

            X_num = 1
            dir_name = ''
            while X_num <= self.total_X_num:
                dir_name += 'X{}-{}'.format(X_num, new_name_comb[X_num - 1])
                if X_num < self.total_X_num:
                    dir_name += '_'

                X_num += 1

            # 数値条件も組み込んで MIN できるように
            other_names = self.name_comb[self.total_X_num:]
            other_labels = self.comb_label[self.total_X_num:]
            if other_names:
                for name, label in zip(other_names, other_labels):
                    name = str(name)
                    if 'solvent' in label.lower():
                        dir_name += f'_Sol-{name}'
                    if 'temperature' in label.lower():
                        dir_name += f'_Temp-{name}'

            self.dir_name_l.append(dir_name)
            self.name_comb_l.append(new_name_comb)

            if dir_name in self.seen:
                self.isDuplicate_l.append(True)
            elif os.path.isdir(os.path.join('..', dir_name)):
                self.isDuplicate_l.append(True)
            else:
                self.isDuplicate_l.append(False)

            return

        next_idx = len(temp_name_enum)
        for name in self.part_X_name_enum_l[next_idx]:
            self.dfs_enumeration(temp_name_enum + [name])
