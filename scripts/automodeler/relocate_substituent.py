import pdb
from time import sleep

from copy import deepcopy
from functools import lru_cache

import numpy as np

import automodeler.translation as translation
from automodeler.input_reader import ReadInput
from automodeler.rotation import XYZ_AxisRotation
from automodeler.rotation import N_AxisRotation


class RelocateSubstituent(ReadInput):
    def __init__(self, input_name):
        super(RelocateSubstituent, self).__init__(input_name)
        self.xyz_rotation = XYZ_AxisRotation()
        self.n_rotation = N_AxisRotation()

    def run(self, c_name_comb):
        # XYZ 軸周りの回転を全探索し, 最適な結合方向を持つ配座を取得
        best_atom_xyz = [[] for i in range(self.total_X_num)]
        
        for X_idx in self.sub_mode_X_inx:
            xyz_best_atom_xyz = self.xyz_axis_opt(X_idx, c_name_comb)
            best_atom_xyz[X_idx] = xyz_best_atom_xyz

        # N 軸周りの回転を 2 回ずつ行って立体障害を最小化
        # 2022-07-01 : 動作おかしいかもしれない
        for itr in range(2):
            for X_idx in self.sub_mode_X_inx:
                n_best_atom_xyz = self.n_axis_opt(X_idx, best_atom_xyz)
                n_best_atom_xyz = [i[:1] + [float(j) for j in i[1:]] for i in n_best_atom_xyz]
                best_atom_xyz[X_idx] = n_best_atom_xyz

        # for i in sum(best_atom_xyz, []):
        #     print(' '.join([str(i) for i in i]))

        return best_atom_xyz

    def xyz_axis_opt(self, X_idx, c_name_comb):
        c_idx = self.X_inx_perm_dict[X_idx]
        name = c_name_comb[c_idx]
        for t_name_atom_xyz in self.locus_cand_name_atom_xyz[c_idx]:
            t_name = t_name_atom_xyz[0]
            t_atom_xyz = t_name_atom_xyz[1]
            if t_name == name:
                atom_xyz = t_atom_xyz
                break

        ghost_atom_xyz = atom_xyz[0]
        ghost_xyz = ghost_atom_xyz[1:]
        target_atom_xyz = atom_xyz[1:]

        root_num = self.root_list_of_each_X[X_idx]
        root_atom_xyz = self.part_root_atom_xyz_dict[root_num]

        X_atom_xyz = self.model_X_atom_xyz[X_idx]
        X_atom = X_atom_xyz[0]
        X_xyz = tuple(X_atom_xyz[1:])

        # 平行移動
        target_atom_xyz, ghost_xyz = translation.translation(root_atom_xyz, X_xyz, 
                                                             target_atom_xyz, ghost_xyz)

        # 回転
        target_atom_xyz = self.xyz_rotation.run(target_atom_xyz, 'angle',
                                                root_atom_xyz=root_atom_xyz,
                                                ghost_xyz=ghost_xyz)

        return target_atom_xyz

    def n_axis_opt(self, X_idx, xyz_best_atom_xyz):
        target_atom_xyz = xyz_best_atom_xyz[X_idx]

        root_num = self.root_list_of_each_X[X_idx]
        root_atom_xyz = self.part_root_atom_xyz_dict[root_num]
        root_xyz = root_atom_xyz[1:]

        cp_xyz_best_atom_xyz = deepcopy(xyz_best_atom_xyz)
        del cp_xyz_best_atom_xyz[X_idx]

        frozen_atom_xyz = sum(cp_xyz_best_atom_xyz, []) + self.model_not_X_atom_xyz
        target_atom_xyz = self.n_rotation.run(target_atom_xyz, frozen_atom_xyz, root_xyz)

        return target_atom_xyz
