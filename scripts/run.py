import pdb

import sys
sys.setrecursionlimit(10**9)

from automodeler.model_generator import ModelGenerator


class DFS:
    def __init__(self):
        self.atom_xyz_info = []

    def run(self, cand_num_comb_l, sub_inx, model):
        if len(cand_num_comb_l) == model.total_X_num:
            dir_name, duplicate, atom_xyz = model.run(cand_num_comb_l)

            self.atom_xyz_info.append([dir_name, atom_xyz])

            print('Directory name : ' + dir_name)
            return

        sub_inx += 1
        for cand_num in model.locus_gene_list[sub_inx]:
            self.run(cand_num_comb_l + [cand_num], sub_inx, model)

    def summarize(self):
        xyz_file = open('All_structure.xyz', 'w')
        for dir_name, atom_xyz in self.atom_xyz_info:
            xyz_file.write(str(len(atom_xyz)) + '\n')
            xyz_file.write(dir_name + '\n')
            for each_atom_xyz in atom_xyz:
                atom = each_atom_xyz[0].ljust(12)
                xyz = each_atom_xyz[1:]
                xyz = ['{:.1000f}'.format(float(k))[:14] for k in xyz]
                space = ' ' * 11
                xyz_file.write(atom + space.join(xyz))
                xyz_file.write('\n')

            xyz_file.write('\n')

        xyz_file.close()


def run(population='all'):
    print('Enter input name (xxx of xxx.com)')
    input_name = input().split('.')[0]
    model = ModelGenerator(input_name)

    dfs = DFS()

    if population == 'all':
        dfs.run([], -1, model)
        dfs.summarize()
    else:
        for individual in population:
            dir_name, duplicate, atom_xyz = model.run(individual)

    print('\nFinish\n')


if __name__ == '__main__':
    run()
