# train models

# Discriminative methods

# Make directory for evaluations
# mkdir -p Evaluations

# # eval DGCNN backbone and SR1 dataset
# python -m torch.distributed.launch --nproc_per_node=1 classifiers/trainer_ddp_cla_md.py --config cfgs/dgcnn-cla.yaml --exp_name DGCNN_CE_SR1 --src SR1 --loss CE -mode eval --ckpt_path outputs/DGCNN_CE_SR1/models/model_best.pth >> Evaluations/DGCNN_CE_SR1.txt

# # # eval DGCNN backbone and SR2 dataset
# python -m torch.distributed.launch --nproc_per_node=1 classifiers/trainer_ddp_cla_md.py --config cfgs/dgcnn-cla.yaml --exp_name DGCNN_CE_SR2 --src SR2 --loss CE -mode eval --ckpt_path outputs/DGCNN_CE_SR2/models/model_best.pth >> Evaluations/DGCNN_CE_SR2.txt

# # eval PointNet++ backbone and SR1 dataset
# python -m torch.distributed.launch --nproc_per_node=1 classifiers/trainer_ddp_cla_md.py --config cfgs/pn2-msg.yaml --exp_name PN2_CE_SR1 --src SR1 --loss CE -mode eval --ckpt_path outputs/PN2_CE_SR1/models/model_best.pth > Evaluations/PN2_CE_SR1.txt

# # eval with PointNet++ backbone and SR2 dataset
# python -m torch.distributed.launch --nproc_per_node=1 classifiers/trainer_ddp_cla_md.py --config cfgs/pn2-msg.yaml --exp_name PN2_CE_SR2 --src SR2 --loss CE -mode eval --ckpt_path outputs/PN2_CE_SR2/models/model_best.pth > Evaluations/PN2_CE_SR2.txt


# # Representation and Distance Based Models

# ##ARPL+CS

# # DID NOT WORK


# ## Cosine proto

# # eval DGCNN backbone and SR1 dataset
# python -m torch.distributed.launch --nproc_per_node=1 classifiers/trainer_ddp_cla_md.py --config cfgs/dgcnn-cla.yaml --exp_name DGCNN_cosine_SR1 --src SR1 --loss cosine -mode eval --ckpt_path outputs/DGCNN_cosine_SR1/models/model_best.pth > Evaluations/DGCNN_cosine_SR1.txt

# # eval DGCNN backbone and SR2 dataset
# python -m torch.distributed.launch --nproc_per_node=1 classifiers/trainer_ddp_cla_md.py --config cfgs/dgcnn-cla.yaml --exp_name DGCNN_cosine_SR2 --src SR2 --loss cosine -mode eval --ckpt_path outputs/DGCNN_cosine_SR2/models/model_best.pth > Evaluations/DGCNN_cosine_SR2.txt

# # eval PointNet++ backbone and SR1 dataset
# python -m torch.distributed.launch --nproc_per_node=1 classifiers/trainer_ddp_cla_md.py --config cfgs/pn2-msg.yaml --exp_name PN2_cosine_SR1 --src SR1 --loss cosine -mode eval --ckpt_path outputs/PN2_cosine_SR1/models/model_best.pth > Evaluations/PN2_cosine_SR1.txt

# # eval with PointNet++ backbone and SR2 dataset
# python -m torch.distributed.launch --nproc_per_node=1 classifiers/trainer_ddp_cla_md.py --config cfgs/pn2-msg.yaml --exp_name PN2_cosine_SR2 --src SR2 --loss cosine -mode eval --ckpt_path outputs/PN2_cosine_SR2/models/model_best.pth > Evaluations/PN2_cosine_SR2.txt

# # ## SubArcFace

# # eval with DGCNN backbone and SR1 dataset
# python -m torch.distributed.launch --nproc_per_node=1 classifiers/trainer_ddp_cla_md.py --config cfgs/dgcnn-cla.yaml --exp_name DGCNN_subarcface_SR1 --src SR1 --loss subcenter_arcface -mode eval --ckpt_path outputs/DGCNN_subarcface_SR1/models/model_best.pth > Evaluations/DGCNN_subarcface_SR1.txt

# # eval with DGCNN backbone and SR2 dataset
# python -m torch.distributed.launch --nproc_per_node=1 classifiers/trainer_ddp_cla_md.py --config cfgs/dgcnn-cla.yaml --exp_name DGCNN_subarcface_SR2 --src SR2 --loss subcenter_arcface -mode eval --ckpt_path outputs/DGCNN_subarcface_SR2/models/model_best.pth > Evaluations/DGCNN_subarcface_SR2.txt

# # eval with PointNet++ backbone and SR1 dataset
# python -m torch.distributed.launch --nproc_per_node=1 classifiers/trainer_ddp_cla_md.py --config cfgs/pn2-msg.yaml --exp_name PN2_subarcface_SR1 --src SR1 --loss subcenter_arcface -mode eval --ckpt_path outputs/PN2_subarcface_SR1/models/model_best.pth > Evaluations/PN2_subarcface_SR1.txt

# # eval with PointNet++ backbone and SR2 dataset
# python -m torch.distributed.launch --nproc_per_node=1 classifiers/trainer_ddp_cla_md.py --config cfgs/pn2-msg.yaml --exp_name PN2_subarcface_SR2 --src SR2 --loss subcenter_arcface -mode eval --ckpt_path outputs/PN2_subarcface_SR2/models/model_best.pth > Evaluations/PN2_subarcface_SR2.txt