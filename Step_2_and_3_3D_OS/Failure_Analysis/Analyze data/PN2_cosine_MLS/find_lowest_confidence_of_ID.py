import numpy as np
import open3d as o3d

src = "SR1"
baseline = "PN2_cosine"
method = "MLS"
data_dir = "results/SR1_data"


src_scores = np.load("results/" + baseline + "/" + src + "/" + method + "/" + src + "_id_scores.npy")
tar1_scores = np.load("results/" + baseline + "/" + src + "/" + method + "/" + src + "_ood1_scores.npy")
tar2_scores = np.load("results/" + baseline + "/" + src + "/" + method + "/" + src + "_ood2_scores.npy")

src_labels = np.load("results/" + baseline + "/" + src + "/" + method + "/" + src + "_id_labels.npy")
tar1_labels = np.load("results/" + baseline + "/" + src + "/" + method + "/" + src + "_ood1_labels.npy")
tar2_labels = np.load("results/" + baseline + "/" + src + "/" + method + "/" + src + "_ood2_labels.npy")

# Find the 10 lowest confidence scores for the ID domain

src_MSP_scores_10_lowest_keys = np.argsort(src_scores)[:10]
src_MSP_scores_10_lowest_data = []

for i in src_MSP_scores_10_lowest_keys:

    print(i, src_scores[i], src_labels[i])

    filename = data_dir + "/" + str(src) + "_id_data_" + str(i) + ".npy"

    points = np.load(filename)
    points = points.reshape(-1, 3)
    
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)
    src_MSP_scores_10_lowest_data.append(pcd)

    o3d.visualization.draw_geometries([pcd])
