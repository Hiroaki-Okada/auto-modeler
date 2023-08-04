from math import radians

import numpy as np


class RotationMatrix:
    def define(self, deg):
        self.rad = radians(deg)
        self.sin = np.sin(self.rad)
        self.cos = np.cos(self.rad)

    def rot_matrix_x(self, deg):
        self.define(deg)
        R_x = np.array([[1, 0, 0],
                        [0, self.cos, -self.sin],
                        [0, self.sin, self.cos]])
        return R_x

    def rot_matrix_y(self, deg):
        self.define(deg)
        R_y = np.array([[self.cos, 0, self.sin],
                        [0, 1, 0],
                        [-self.sin, 0, self.cos]])
        return R_y

    def rot_matrix_z(self, deg):
        self.define(deg)
        R_z = np.array([[self.cos, -self.sin, 0],
                        [self.sin, self.cos, 0],
                        [0, 0, 1]])
        return R_z

    def rot_matrix_n(self, deg, n_unit_vec):
        self.define(deg)

        nx = n_unit_vec[0]
        ny = n_unit_vec[1]
        nz = n_unit_vec[2]

        R_n = np.array([[self.cos + nx ** 2 * (1 - self.cos),
                         nx * ny * (1 - self.cos) - nz * self.sin,
                         nz * nx * (1 - self.cos) + ny * self.sin],
                        [nx * ny * (1 - self.cos) + nz * self.sin,
                         self.cos + ny ** 2 * (1 - self.cos),
                         ny * nz * (1 - self.cos) - nx * self.sin],
                        [nz * nx * (1 - self.cos) - ny * self.sin,
                         ny * nz * (1 - self.cos) + nx * self.sin,
                         self.cos + nz ** 2 * (1 - self.cos)]])

        return R_n
