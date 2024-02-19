# train models

# Discriminative methods

# train with DGCNN backbone and SR1 dataset
python -m torch.distributed.launch --nproc_per_node=1 classifiers/trainer_ddp_cla_md.py --config cfgs/dgcnn-cla.yaml --exp_name DGCNN_CE_SR1 --src SR1 --loss CE --batch_size 10

# train with DGCNN backbone and SR2 dataset
python -m torch.distributed.launch --nproc_per_node=1 classifiers/trainer_ddp_cla_md.py --config cfgs/dgcnn-cla.yaml --exp_name DGCNN_CE_SR2 --src SR2 --loss CE --batch_size 10

# train with PointNet++ backbone and SR1 dataset
# python -m torch.distributed.launch --nproc_per_node=1 classifiers/trainer_ddp_cla_md.py --config cfgs/pn2-msg.yaml --exp_name PN2_CE_SR1 --src SR1 --loss CE --batch_size 10

# train with PointNet++ backbone and SR2 dataset
#python -m torch.distributed.launch --nproc_per_node=1 classifiers/trainer_ddp_cla_md.py --config cfgs/pn2-msg.yaml --exp_name PN2_CE_SR2 --src SR2 --loss CE --batch_size 10


# Representation and Distance Based Models

##ARPL+CS
# train with DGCNN backbone and SR1 dataset
# Fungerer ikke
#python -m torch.distributed.launch --nproc_per_node=1 classifiers/trainer_ddp_cla_md.py --config cfgs/dgcnn-cla.yaml --exp_name DGCNN_ARPL_CS_SR1 --src SR1 --loss ARPL --cs --batch_size 2

# train with DGCNN backbone and SR2 dataset
# Fungerer ikke
#python -m torch.distributed.launch --nproc_per_node=1 classifiers/trainer_ddp_cla_md.py --config cfgs/dgcnn-cla.yaml --exp_name DGCNN_ARPL_CS_SR2 --src SR2 --loss ARPL --cs --batch_size 2

#train with PointNet++ backbone and SR1 dataset
# # Fungerer ikke
# python -m torch.distributed.launch --nproc_per_node=1 classifiers/trainer_ddp_cla_md.py --config cfgs/pn2-msg.yaml --exp_name PN2_ARPL_CS_SR1 --src SR1 --loss ARPL --cs --batch_size 5

# #train with PointNet++ backbone and SR2 dataset
# # Fungerer ikke
# python -m torch.distributed.launch --nproc_per_node=1 classifiers/trainer_ddp_cla_md.py --config cfgs/pn2-msg.yaml --exp_name PN2_ARPL_CS_SR2 --src SR2 --loss ARPL --cs --batch_size 5

## Cosine proto

# train with DGCNN backbone and SR1 dataset
# python -m torch.distributed.launch --nproc_per_node=1 classifiers/trainer_ddp_cla_md.py --config cfgs/dgcnn-cla.yaml --exp_name DGCNN_cosine_SR1 --src SR1 --loss cosine --batch_size 10

# train with DGCNN backbone and SR2 dataset
# python -m torch.distributed.launch --nproc_per_node=1 classifiers/trainer_ddp_cla_md.py --config cfgs/dgcnn-cla.yaml --exp_name DGCNN_cosine_SR2 --src SR2 --loss cosine --batch_size 10

# train with PointNet++ backbone and SR1 dataset
# python -m torch.distributed.launch --nproc_per_node=1 classifiers/trainer_ddp_cla_md.py --config cfgs/pn2-msg.yaml --exp_name PN2_cosine_SR1 --src SR1 --loss cosine --batch_size 10

# # train with PointNet++ backbone and SR2 dataset
# python -m torch.distributed.launch --nproc_per_node=1 classifiers/trainer_ddp_cla_md.py --config cfgs/pn2-msg.yaml --exp_name PN2_cosine_SR2 --src SR2 --loss cosine --batch_size 10

# ## SubArcFace

# # train with DGCNN backbone and SR1 dataset
# python -m torch.distributed.launch --nproc_per_node=1 classifiers/trainer_ddp_cla_md.py --config cfgs/dgcnn-cla.yaml --exp_name DGCNN_subarcface_SR1 --src SR1 --loss subcenter_arcface --batch_size 10

# # train with DGCNN backbone and SR2 dataset
# python -m torch.distributed.launch --nproc_per_node=1 classifiers/trainer_ddp_cla_md.py --config cfgs/dgcnn-cla.yaml --exp_name DGCNN_subarcface_SR2 --src SR2 --loss subcenter_arcface --batch_size 10

# # train with PointNet++ backbone and SR1 dataset
# python -m torch.distributed.launch --nproc_per_node=1 classifiers/trainer_ddp_cla_md.py --config cfgs/pn2-msg.yaml --exp_name PN2_subarcface_SR1 --src SR1 --loss subcenter_arcface --batch_size 10

# # train with PointNet++ backbone and SR2 dataset
# python -m torch.distributed.launch --nproc_per_node=1 classifiers/trainer_ddp_cla_md.py --config cfgs/pn2-msg.yaml --exp_name PN2_subarcface_SR2 --src SR2 --loss subcenter_arcface --batch_size 10