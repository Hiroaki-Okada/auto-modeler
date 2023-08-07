import pdb

from functools import lru_cache

from automodeler.input_reader import ReadInput


class RelocateAtom(ReadInput):
    def __init__(self, input_name):
        super(RelocateAtom, self).__init__(input_name)

    @lru_cache(maxsize=None)
    def run(self, c_name_comb):
        best_atom_xyz = [[] for i in range(self.total_X_num)]
        for X_idx in self.atom_mode_X_inx:
            best_atom_xyz[X_idx] = self.get_atom_xyz(X_idx, c_name_comb)

        return best_atom_xyz

    def get_atom_xyz(self, X_idx, c_name_comb):
        c_idx = self.X_inx_perm_dict[X_idx]
        name = c_name_comb[c_idx]
        for t_name_atom_xyz in self.locus_cand_name_atom_xyz[c_idx]:
            t_name = t_name_atom_xyz[0]
            t_atom_xyz = t_name_atom_xyz[1]
            if t_name == name:
                # t_atom_xyzは多次元配列なので, 原子名には[0][0]でアクセス
                atom_name = t_atom_xyz[0][0]
                break

        ref_atom_xyz = self.model_X_atom_xyz[X_idx]
        best_atom_xyz = [[atom_name] + ref_atom_xyz[1:]]

        return best_atom_xyz