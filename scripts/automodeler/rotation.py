import pdb
from time import sleep

from functools import lru_cache

import numpy as np
from scipy.spatial.distance import cdist

from automodeler.rotation_matrix import RotationMatrix


class OptXYZ():
    # ベクトル間角度を最小化する回転行列をターゲットに作用させる
    def minimize_angle(self, angle_l, deg_l, target_xyz, target_atom, rep_xyz):
        min_angle_inx = angle_l.index(min(angle_l))

        optimal_deg = deg_l[min_angle_inx]
        optimal_deg_x = optimal_deg[0]
        optimal_deg_y = optimal_deg[1]
        optimal_deg_z = optimal_deg[2]

        Rx = self.rot_matrix.rot_matrix_x(optimal_deg_x)
        Ry = self.rot_matrix.rot_matrix_y(optimal_deg_y)
        Rz = self.rot_matrix.rot_matrix_z(optimal_deg_z)

        # rep周りに回転させるので, repが原点に来るように平行移動しておく
        transition_xyz = target_xyz - rep_xyz

        x_rotated_xyz = self.rotation(Rx, transition_xyz)
        y_rotated_xyz = self.rotation(Ry, x_rotated_xyz)
        z_rotated_xyz = self.rotation(Rz, y_rotated_xyz)

        # repを元の場所に戻すように再び平行移動
        z_rotated_xyz = np.array(z_rotated_xyz)
        z_rotated_xyz += rep_xyz

        target_atom = target_atom.reshape([len(target_atom), 1])
        opt_atom_xyz = np.concatenate([target_atom, z_rotated_xyz], 1).tolist()

        return opt_atom_xyz

    def maximize_dist(self, rot_xyz_l, dist_matrix_l, dist_sum_l, target_atom, min_bond_len=3.0):
        opt_xyz = []
        while opt_xyz == []:
            max_dist_sum = 0
            for cand_xyz, dist_matrix, dist_sum in zip(rot_xyz_l, dist_matrix_l, dist_sum_l):
                bond_cnt = np.count_nonzero(dist_matrix <= min_bond_len)

                # 置換基モード : 置換基がroot原子に結合しているのでbond_cnt == 1 は確定
                #                bond_cnt >= 2の場合は正しくない結合があるので棄却
                # 分子モード   : bond_cnt == 0 が基本

                # if bond_cnt >= 2:
                #     continue

                # rot_time = 360 // self.deg_step
                # if len(rot_xyz_l) == rot_time and bond_cnt >= 2:
                #     continue
                # if len(rot_xyz_l) == rot_time ** 3 and bond_cnt >= 1:
                #     continue

                if bond_cnt >= 1:
                    continue

                if dist_sum > max_dist_sum:
                    max_dist_sum = dist_sum
                    opt_xyz = cand_xyz

            min_bond_len -= 0.1

        target_atom = target_atom.reshape([len(target_atom), 1])
        opt_atom_xyz = np.concatenate([target_atom, opt_xyz], 1).tolist()

        return opt_atom_xyz


class XYZ_AxisRotation(OptXYZ):
    def __init__(self, deg_step=24):
        self.deg_step = deg_step
        self.rot_matrix = RotationMatrix()

    @lru_cache(maxsize=None)
    def run(self, target_atom_xyz, opt_type, frozen_atom_xyz=(), root_atom_xyz=[], ghost_xyz=[]):
        target_atom_xyz = np.array(target_atom_xyz)
        target_atom = target_atom_xyz[:, 0]
        target_xyz = target_atom_xyz[:, 1:].astype(np.float64)
        rep_xyz = target_xyz[0]

        if frozen_atom_xyz != ():
            frozen_atom_xyz = np.array(frozen_atom_xyz)
            frozen_xyz = frozen_atom_xyz[:, 1:].astype(np.float64)

        if opt_type == 'angle':
            root_atom_xyz = np.array(root_atom_xyz)
            root_xyz = root_atom_xyz[1:].astype(np.float64)

            ghost_xyz = np.array([ghost_xyz]).astype(np.float64)

            rot_ghost_xyz_l = self.xyz_rotation(ghost_xyz, rep_xyz)
            angle_l, deg_l = self.get_angle_deg(rot_ghost_xyz_l, root_xyz, rep_xyz)
            opt_atom_xyz = self.minimize_angle(angle_l, deg_l, target_xyz, target_atom, rep_xyz)

            print(len(set(angle_l)), min(angle_l))

        elif opt_type == 'distance':
            rot_xyz_l = self.xyz_rotation(target_xyz, rep_xyz)
            dist_matrix_l, dist_sum_l = self.get_dist(rot_xyz_l, frozen_xyz)
            opt_atom_xyz = self.maximize_dist(rot_xyz_l, dist_matrix_l, dist_sum_l, target_atom)

        return opt_atom_xyz

    def rotation(self, rot_matrix, xyz):
        rot_xyz = []
        for each_xyz in xyz:
            rot_xyz.append(np.dot(rot_matrix, each_xyz))

        return rot_xyz

    # 各回転行列を作用させた場合のghost_atomの座標のリストを取得
    def xyz_rotation(self, target_xyz, rep_xyz):
        Rx_l = [self.rot_matrix.rot_matrix_x(deg) for deg in range(0, 360, self.deg_step)]
        Ry_l = [self.rot_matrix.rot_matrix_y(deg) for deg in range(0, 360, self.deg_step)]
        Rz_l = [self.rot_matrix.rot_matrix_z(deg) for deg in range(0, 360, self.deg_step)]

        # rep周りに回転させるので, repが原点に来るようにあらかじめ平行移動しておく
        trans_target_xyz = target_xyz - rep_xyz

        rot_xyz_l = []
        for Rx in Rx_l:
            x_rotated_xyz = self.rotation(Rx, trans_target_xyz)
            for Ry in Ry_l:
                y_rotated_xyz = self.rotation(Ry, x_rotated_xyz)
                for Rz in Rz_l:
                    z_rotated_xyz = self.rotation(Rz, y_rotated_xyz)
                    z_rotated_xyz = np.array(z_rotated_xyz)
                    # repが元の位置に戻るように再び平行移動
                    z_rotated_xyz += rep_xyz
                    rot_xyz_l.append(z_rotated_xyz)

        return rot_xyz_l

    def get_angle_deg(self, rot_xyz_l, root_xyz, rep_xyz):
        angle_l, deg_l = [], []

        itr = -1
        base_num = 360 // self.deg_step
        for xyz in rot_xyz_l:
            #xyzが二次元配列になっているので一次元配列にする
            xyz = xyz[0]

            # rep-rootベクトルとrep-ghostベクトルのなす角度を記録
            vec1 = root_xyz - rep_xyz
            vec2 = xyz - rep_xyz
            l1 = np.linalg.norm(vec1)
            l2 = np.linalg.norm(vec2)
            inner_product = np.inner(vec1, vec2)

            theta = np.rad2deg(np.arccos(inner_product / (l1 * l2)))
            angle_l.append(theta)

            # (360 / self.deg_step)進数で考えて角度の組み合わせをO(1)で計算し, 記録
            itr += 1
            num = itr
            deg_z = (num % base_num) * self.deg_step
            num //= base_num
            deg_y = (num % base_num) * self.deg_step
            num //= base_num
            deg_x = (num % base_num) * self.deg_step

            deg_l.append((deg_x, deg_y, deg_z))

        return angle_l, deg_l

    # 2022-06-30 : 分子モードの時に, 置換基もfrozen_xyzに入ってる？ --> 入ってた
    def get_dist(self, rot_xyz_l, frozen_xyz):
        dist_matrix_l, dist_sum_l = [], []
        for xyz in rot_xyz_l:
            dist_matrix = cdist(xyz, frozen_xyz)
            dist_matrix_l.append(dist_matrix)
            dist_sum = np.sum(dist_matrix)
            dist_sum_l.append(dist_sum)

        return dist_matrix_l, dist_sum_l


class N_AxisRotation(OptXYZ):
    def __init__(self, deg_step=10):
        self.deg_step = deg_step
        self.rot_matrix = RotationMatrix()

    def run(self, target_atom_xyz, frozen_atom_xyz, root_xyz):
        target_atom_xyz = np.array(target_atom_xyz)
        target_atom = target_atom_xyz[:, 0]
        target_xyz = target_atom_xyz[:, 1:].astype(np.float64)
        rep_xyz = target_xyz[0]

        frozen_atom_xyz = np.array(frozen_atom_xyz)
        frozen_xyz = frozen_atom_xyz[:, 1:].astype(np.float64)

        n_vec = rep_xyz - root_xyz
        n_unit_vec = n_vec / np.linalg.norm(n_vec)

        rot_xyz_l, dist_matrix_l, dist_sum_l = self.n_rotation(n_unit_vec, target_xyz, rep_xyz, frozen_xyz)
        opt_atom_xyz = self.maximize_dist(rot_xyz_l, dist_matrix_l, dist_sum_l, target_atom)

        # for i in np.array(rot_xyz_l)[:, 1].tolist():
        #     print('H ' + ' '.join([str(j) for j in i]))

        return opt_atom_xyz

    def rotation(self, rot_matrix, xyz):
        rot_xyz = []
        for each_xyz in xyz:
            rot_xyz.append(np.dot(rot_matrix, each_xyz))

        return rot_xyz

    def n_rotation(self, n_unit_vec, target_xyz, rep_xyz, frozen_xyz):
        Rn_l = [self.rot_matrix.rot_matrix_n(deg, n_unit_vec) for deg in range(0, 360, self.deg_step)]

        # rep周りに回転させるので, repが原点に来るようにあらかじめ平行移動しておく
        trans_xyz = target_xyz - rep_xyz

        rot_xyz_l, dist_matrix_l, dist_sum_l = [], [], []
        for Rn in Rn_l:
            rotated_xyz = self.rotation(Rn, trans_xyz)
            rotated_xyz = np.array(rotated_xyz)
            # repが元の位置に戻るように再び平行移動
            rotated_xyz += rep_xyz

            dist_matrix = cdist(rotated_xyz, frozen_xyz)
            dist_sum = np.sum(dist_matrix)

            rot_xyz_l.append(rotated_xyz)
            dist_matrix_l.append(dist_matrix)
            dist_sum_l.append(dist_sum)

        return rot_xyz_l, dist_matrix_l, dist_sum_l
