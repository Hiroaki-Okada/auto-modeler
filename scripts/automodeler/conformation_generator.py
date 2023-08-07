import pdb

from copy import deepcopy

from automodeler.input_reader import ReadInput
from automodeler.relocate_atom import RelocateAtom
from automodeler.relocate_substituent import RelocateSubstituent
from automodeler.relocate_molecule import RelocateMolecule
from automodeler.benchmark import visualize_model


class ConformationGenerator(ReadInput):
    def __init__(self, input_name):
        super(ConformationGenerator, self).__init__(input_name)
        self.relocate_atom = RelocateAtom(input_name)
        self.relocate_sub = RelocateSubstituent(input_name)
        self.relocate_mol = RelocateMolecule(input_name)

    def run(self, c_name_comb):
        self.c_name_comb = c_name_comb
        self.generated_coordinate = [[] for i in range(self.total_X_num)]

        self.atom_mode()
        self.substituent_mode()
        self.molecule_mode()

        self.generated_coordinate = sum(self.generated_coordinate, [])
        # visualize_model(self.model_not_X_atom_xyz, self.generated_coordinate)

        return self.generated_coordinate

    def atom_mode(self):
        best_atom_xyz = self.relocate_atom.run(self.c_name_comb)
        for X_idx in self.atom_mode_X_inx:
            self.generated_coordinate[X_idx] = best_atom_xyz[X_idx]

    def substituent_mode(self):
        best_atom_xyz = self.relocate_sub.run(self.c_name_comb)
        for X_idx in self.sub_mode_X_inx:
            self.generated_coordinate[X_idx] = best_atom_xyz[X_idx]

    def molecule_mode(self):
        ref_atom_xyz = sum(self.generated_coordinate, [])
        best_atom_xyz = self.relocate_mol.run(self.c_name_comb, ref_atom_xyz)
        for X_idx in self.mol_mode_X_inx:
            self.generated_coordinate[X_idx] = best_atom_xyz[X_idx]
