import pdb

import sys
sys.setrecursionlimit(10**9)

from automodeler.model_generator import ModelGenerator


class DFS:
    def __init__(self, model):
        self.model = model
        self.all_generated_atom_xyz = []

    # DFSによる組み合わせ全探索
    # 各組み合わせはインプットで指定された整数の配列形式で扱われる
    def run(self, cand_num_comb_l, sub_idx):
        if len(cand_num_comb_l) == self.model.total_X_num:
            dir_name, duplicate, atom_xyz = self.model.run(cand_num_comb_l)
            self.all_generated_atom_xyz.append([dir_name, atom_xyz])
            print('Directory name :', dir_name)
            return

        sub_idx += 1
        for cand_num in self.model.locus_gene_list[sub_idx]:
            self.run(cand_num_comb_l + [cand_num], sub_idx)

    # 作成した全ての構造をxyzファイルにまとめる
    def summarize(self, space=' '*11):
        xyz_file = open('All_structure.xyz', 'w')
        for dir_name, atom_xyz in self.all_generated_atom_xyz:
            xyz_file.write(dir_name + '\n')
            for each_atom_xyz in atom_xyz:
                atom = each_atom_xyz[0].ljust(12)
                xyz = each_atom_xyz[1:]
                xyz = ['{:.1000f}'.format(float(k))[:14] for k in xyz]
                xyz_file.write(atom + space.join(xyz))
                xyz_file.write('\n')

            xyz_file.write('\n')

        xyz_file.close()


def run(population='all'):
    print('\nEnter input name (xxx of xxx.com)')
    # input_name = input().split('.')[0]
    input_name = 'read'
    model = ModelGenerator(input_name)

    dfs = DFS(model=model)

    if population == 'all':
        dfs.run([], -1)
        dfs.summarize()
    else:
        for individual in population:
            dir_name, duplicate, atom_xyz = model.run(individual)

    print('\nFinish running\n')


if __name__ == '__main__':
    run()
