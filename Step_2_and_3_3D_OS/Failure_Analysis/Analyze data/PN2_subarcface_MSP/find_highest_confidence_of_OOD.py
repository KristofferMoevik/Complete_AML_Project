import numpy as np
import open3d as o3d

import numpy as np
import open3d as o3d

src = "SR1"
baseline = "PN2_subarcface"
method = "MSP"
data_dir = "results/SR1_data"

src_scores = np.load("results/" + baseline + "/" + src + "/" + method + "/" + src + "_id_scores.npy")
tar1_scores = np.load("results/" + baseline + "/" + src + "/" + method + "/" + src + "_ood1_scores.npy")
tar2_scores = np.load("results/" + baseline + "/" + src + "/" + method + "/" + src + "_ood2_scores.npy")

src_labels = np.load("results/" + baseline + "/" + src + "/" + method + "/" + src + "_id_labels.npy")
tar1_labels = np.load("results/" + baseline + "/" + src + "/" + method + "/" + src + "_ood1_labels.npy")
tar2_labels = np.load("results/" + baseline + "/" + src + "/" + method + "/" + src + "_ood2_labels.npy")

# Find the 10 highest confidence scores for the OOD1 domain

tar1_scores_10_highest_keys = np.argsort(tar1_scores)[-10:]
tar1_scores_10_highest_data = []

for i in tar1_scores_10_highest_keys:

    print(i, tar1_scores[i], tar1_labels[i])
    filename = data_dir + "/" + str(src) + "_ood1_data_" + str(i) + ".npy"

    points = np.load(filename)
    points = points.reshape(-1, 3)
    
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)
    tar1_scores_10_highest_data.append(pcd)

    o3d.visualization.draw_geometries([pcd])
    
