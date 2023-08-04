import pdb

import numpy as np
from functools import lru_cache

import automodeler.elementdata as elementdata
element_data = elementdata.ElementData()

# 本メソッドでは, 置換基を平行移動して化学的に正しい座標に配置する
# atom_xyz は置換基の座標であり, 現状ではインプットで与えられた座標そのものである
# これを, 結合元の原子(root_atom)からX_atom方向へ共有結合半径分だけ離れた位置に平行移動する
# また, 置換基を中性化するために加えられている水素原子(ghost_atom)も同様に平行移動しておく
# ここで, 2点を通る直線のベクトル方程式を考える
# 直線AB上の点Pの位置ベクトルpについて考えると, p = (1-t)*a + t*b (tは媒介変数)
# これを利用し, まずroot_atomとX_atom間の距離が望みの共有結合半径になるX_atomの座標:pointを求める
# 続いて, 置換基の代表原子の座標(rep_atom_xyz)とpointの座標差分を求め, 平行移動行列を求める
# この行列を atom_xyzとghost_xyzに作用させれば, 平行移動が完了する

@lru_cache(maxsize=None)
def translation(root_atom_xyz, X_xyz, atom_xyz, ghost_xyz):
    root_atom = root_atom_xyz[0]
    root_xyz = root_atom_xyz[1:]

    atom_xyz = [list(i) for i in atom_xyz]
    rep_atom = atom_xyz[0][0]
    rep_xyz = np.array(atom_xyz[0][1:])

    # ハッシュのためにタプルになっていたが中身を変更したいのでリストにする
    ghost_xyz = list(ghost_xyz)

    # root_atom = X のときの処理を追加したい
    covalent_dist = element_data.CovalentRadius[root_atom] + \
                    element_data.CovalentRadius[rep_atom]

    t = 0.0
    dist = 0.0
    while dist < covalent_dist:
        t += 0.05
        point = []
        for i, j in zip(root_xyz, X_xyz):
            point.append((1 - t) * i + t * j)

        point = np.array(point)
        dist = np.linalg.norm(root_xyz - point)
        # print('X ' + ' '.join([str(i) for i in point]))

    moving_dist = point - rep_xyz
    for i in range(len(atom_xyz)):
        for inx in range(1, 4):
            atom_xyz[i][inx] += moving_dist[inx - 1]

    for inx in range(3):
        ghost_xyz[inx] += moving_dist[inx]

    atom_xyz = tuple([tuple(i) for i in atom_xyz])
    ghost_xyz = tuple(ghost_xyz)

    return atom_xyz, ghost_xyz
