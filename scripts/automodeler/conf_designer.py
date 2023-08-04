import pdb

from copy import deepcopy

from automodeler.input_reader import ReadInput
from automodeler.relocate_atom import RelocateAtom
from automodeler.relocate_substituent import RelocateSubstituent
from automodeler.relocate_molecule import RelocateMolecule


class ConfDesigner(ReadInput):
    def __init__(self, input_name):
        super(ConfDesigner, self).__init__(input_name)
        self.relocate_atom = RelocateAtom(input_name)
        self.relocate_sub = RelocateSubstituent(input_name)
        self.relocate_mol = RelocateMolecule(input_name)

    def run(self, c_name_comb):
        self.c_name_comb = c_name_comb
        self.model_atom_xyz = [[] for i in range(self.total_X_num)]

        self.atom_mode()
        self.substituent_mode()
        self.molecule_mode()

        self.model_atom_xyz = sum(self.model_atom_xyz, [])

        # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
        # for i in self.model_not_X_atom_xyz:
        #     print(' '.join([str(j) for j in i]))
        # for i in self.model_atom_xyz:
        #     print(' '.join([str(j) for j in i]))

        # exit()
        # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

        return self.model_atom_xyz

    def atom_mode(self):
        opt_atom_xyz = self.relocate_atom.run(self.c_name_comb)
        for X_inx in self.atom_mode_X_inx:
            self.model_atom_xyz[X_inx] = opt_atom_xyz[X_inx]

    def substituent_mode(self):
        opt_atom_xyz = self.relocate_sub.run(self.c_name_comb)
        for X_inx in self.sub_mode_X_inx:
            self.model_atom_xyz[X_inx] = opt_atom_xyz[X_inx]

    def molecule_mode(self):
        ref_atom_xyz = sum(self.model_atom_xyz, [])
        opt_atom_xyz = self.relocate_mol.run(self.c_name_comb, ref_atom_xyz)
        for X_inx in self.mol_mode_X_inx:
            self.model_atom_xyz[X_inx] = opt_atom_xyz[X_inx]
