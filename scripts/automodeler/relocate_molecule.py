import pdb

from copy import deepcopy
from functools import lru_cache
import numpy as np

from automodeler.input_reader import ReadInput
from automodeler.rotation import XYZ_AxisRotation


class RelocateMolecule(ReadInput):
    def __init__(self, input_name):
        super().__init__(input_name)
        self.xyz_rotation = XYZ_AxisRotation()

    def run(self, c_name_comb, ref_atom_xyz):
        opt_atom_xyz = [[] for i in range(self.total_X_num)]
        for X_inx in self.mol_mode_X_inx:
            xyz_opt_atom_xyz = self.xyz_axis_opt(X_inx, ref_atom_xyz, c_name_comb)
            xyz_opt_atom_xyz = [i[:1] + [float(j) for j in i[1:]] for i in xyz_opt_atom_xyz]
            opt_atom_xyz[X_inx] = xyz_opt_atom_xyz

        return opt_atom_xyz

    def translation(self, atom_xyz, X_xyz):
        atom_xyz = [list(i) for i in atom_xyz]
        rep_xyz = np.array(atom_xyz[0][1:])
        X_xyz = np.array(X_xyz)

        moving_dist = X_xyz - rep_xyz
        for i in range(len(atom_xyz)):
            for inx in range(1, 4):
                atom_xyz[i][inx] += moving_dist[inx - 1]

        atom_xyz = tuple([tuple(i) for i in atom_xyz])

        return atom_xyz

    def xyz_axis_opt(self, X_inx, ref_atom_xyz, c_name_comb):
        c_inx = self.X_inx_perm_dict[X_inx]
        name = c_name_comb[c_inx]
        for t_name_atom_xyz in self.locus_cand_name_atom_xyz[c_inx]:
            t_name = t_name_atom_xyz[0]
            t_atom_xyz = t_name_atom_xyz[1]
            if t_name == name:
                target_atom_xyz = t_atom_xyz
                break

        X_atom_xyz = self.model_X_atom_xyz[X_inx]
        X_atom = X_atom_xyz[0]
        X_xyz = tuple(X_atom_xyz[1:])

        frozen_atom_xyz = ref_atom_xyz + self.model_not_X_atom_xyz

        for mol_X_inx in self.mol_mode_X_inx:
            atom_xyz = self.model_X_atom_xyz[mol_X_inx]
            if atom_xyz[0] != X_atom:
                frozen_atom_xyz.append(atom_xyz)

        frozen_atom_xyz = tuple([tuple(i) for i in frozen_atom_xyz])

        target_atom_xyz = self.translation(target_atom_xyz, X_xyz)
        target_atom_xyz = self.xyz_rotation.run(target_atom_xyz, 'distance', frozen_atom_xyz=frozen_atom_xyz)

        return target_atom_xyz
