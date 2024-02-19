import sys
import os
import warnings
import numpy as np

sys.path.append(os.getcwd())
import os.path as osp
import time
from torch.cuda.amp import GradScaler, autocast
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data.distributed import DistributedSampler
from torch.utils.data import DataLoader
from torchvision import transforms
from utils.utils import *
from utils.dist import *
# noinspection PyUnresolvedReferences
from utils.data_utils import H5_Dataset
from datasets.modelnet import *
from datasets.scanobject import *
from models.classifiers import Classifier
from utils.ood_utils import get_confidence, eval_ood_sncore, iterate_data_odin, \
    iterate_data_energy, iterate_data_gradnorm, iterate_data_react, estimate_react_thres, print_ood_output, \
    get_penultimate_feats, get_network_output
import wandb
from base_args import add_base_args
from sklearn.metrics import accuracy_score, balanced_accuracy_score
from models.common import convert_model_state, logits_entropy_loss
from models.ARPL_utils import Generator, Discriminator
from classifiers.common import train_epoch_cla, train_epoch_rsmix_exposure, train_epoch_cs


def save_data_and_scores(id_loader, ood1_loader, ood2_loader, src_labels, tar1_labels, tar2_labels, src_MSP_scores, tar1_MSP_scores, tar2_MSP_scores, baseline, method, src, corruption):
    # save data and scores
    save_dir = f"results/{baseline}/{src}/{method}"
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    data_dir = "results/SR1_data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    # save scores
    print("Saving scores to ", save_dir)
    np.save(os.path.join(save_dir, f"{src}_id_scores.npy"), src_MSP_scores.cpu().numpy())
    np.save(os.path.join(save_dir, f"{src}_ood1_scores.npy"), tar1_MSP_scores.cpu().numpy())
    np.save(os.path.join(save_dir, f"{src}_ood2_scores.npy"), tar2_MSP_scores.cpu().numpy())

    # save labels
    print("Saving labels to ", save_dir)
    np.save(os.path.join(save_dir, f"{src}_id_labels.npy"), src_labels.cpu().numpy())
    np.save(os.path.join(save_dir, f"{src}_ood1_labels.npy"), tar1_labels.cpu().numpy())
    np.save(os.path.join(save_dir, f"{src}_ood2_labels.npy"), tar2_labels.cpu().numpy())

    # save data
    # for i, (data, label) in enumerate(id_loader):
    #     np.save(os.path.join(data_dir, f"{src}_id_data_{i}.npy"), data.cpu().numpy())
    # for i, (data, label) in enumerate(ood1_loader):
    #     np.save(os.path.join(data_dir, f"{src}_ood1_data_{i}.npy"), data.cpu().numpy())
    # for i, (data, label) in enumerate(ood2_loader):
    #     np.save(os.path.join(data_dir, f"{src}_ood2_data_{i}.npy"), data.cpu().numpy())



def get_args():
    parser = argparse.ArgumentParser("OOD on point clouds via contrastive learning")
    parser = add_base_args(parser)

    # experiment specific arguments
    parser.add_argument("--augm_set",
                        type=str, default="rw", help="data augmentation choice", choices=["st", "rw"])
    parser.add_argument("--grad_norm_clip",
                        default=-1, type=float, help="gradient clipping")
    parser.add_argument("--num_points",
                        default=1024, type=int, help="number of points sampled for each object view")
    parser.add_argument("--num_points_test",
                        default=2048, type=int, help="number of points sampled for each SONN object - only for testing")
    parser.add_argument("--wandb_name", type=str, default=None)
    parser.add_argument("--wandb_group", type=str, default="md-2-sonn-augmCorr")
    parser.add_argument("--wandb_proj", type=str, default="benchmark-3d-ood-cla")
    parser.add_argument("--loss", type=str, default="CE",
                        choices=["CE", "CE_ls", "cosface", "arcface", "subcenter_arcface", "ARPL", "cosine"],
                        help="Which loss to use for training. CE is default")
    parser.add_argument("--cs", action='store_true', help="Enable confusing samples for ARPL")
    parser.add_argument("--cs_gan_lr", type=float, default=0.0002, help="Confusing samples GAN lr")
    parser.add_argument("--cs_beta", type=float, default=0.1, help="Beta loss weight for CS")
    parser.add_argument("--save_feats", type=str, default=None, help="Path where to save feats of penultimate layer")

    # Adopt Corrupted data
    # this flag should be set also during evaluation if testing Synth->Real Corr/LIDAR Augmented models
    parser.add_argument("--corruption",
                        type=str, default=None, help="type of corrupted data (lidar,occlusion,all) - default is None")
    args = parser.parse_args()

    args.data_root = os.path.expanduser(args.data_root)
    args.tar1 = "none"
    args.tar2 = "none"

    if args.script_mode == 'eval':
        args.batch_size = 1

    return args


def get_md_react_val_loader(opt):
    print("Building React validation loader...")
    assert opt.script_mode.startswith("eval")
    if not str(opt.src).startswith('SR'):
        raise ValueError(f"Unknown modelnet src: {opt.src}")

    test_data = ModelNet40_OOD(data_root=opt.data_root, train=False, num_points=opt.num_points,
                               class_choice=opt.src, transforms=None)

    print(f"React Val - {opt.src} data len: {len(test_data)}")

    # append corrupted test data
    if opt.corruption:
        print(f"React Val - adding corrupted synthetic data: {opt.corruption}")
        l_corr_data = get_list_corr_data(opt, split='test')  # list of corrupted test datasets
        assert isinstance(l_corr_data, list)
        assert isinstance(l_corr_data[0], data.Dataset)
        l_corr_data.append(test_data)  # appending clean data to list corrupted datasets
        test_data = torch.utils.data.ConcatDataset(l_corr_data)  # concat Dataset
        print(f"React Val - cumulative (clean+corrupted) data len: {len(test_data)}\n")

    val_data = test_data  # note: modelnet synthetic are not used in synth->real eval
    val_loader = DataLoader(val_data, batch_size=opt.batch_size, num_workers=opt.num_workers,
                            worker_init_fn=init_np_seed, shuffle=False, drop_last=False)
    return val_loader


def eval_OOD_with_feats(model, train_loader, src_loader, tar1_loader, tar2_loader, save_feats=None):
    from knn_cuda import KNN
    knn = KNN(k=1, transpose_mode=True)

    print("\n" + "#" * 80)
    print("Computing OOD metrics with distance from train features...")

    # extract penultimate features, compute distances
    train_feats, train_labels = get_penultimate_feats(model, train_loader)
    src_feats, src_labels = get_penultimate_feats(model, src_loader)
    tar1_feats, tar1_labels = get_penultimate_feats(model, tar1_loader)
    tar2_feats, tar2_labels = get_penultimate_feats(model, tar2_loader)
    train_labels = train_labels.cpu().numpy()

    labels_set = set(train_labels)
    prototypes = torch.zeros((len(labels_set), train_feats.shape[1]), device=train_feats.device)
    for idx, lbl in enumerate(labels_set):
        mask = train_labels == lbl
        prototype = train_feats[mask].mean(0)
        prototypes[idx] = prototype

    if save_feats is not None:
        if isinstance(train_loader.dataset, ModelNet40_OOD):
            labels_2_names = {v: k for k, v in train_loader.dataset.class_choice.items()}
        else:
            labels_2_names = {}

        output_dict = {}
        output_dict["labels_2_names"] = labels_2_names
        output_dict["train_feats"], output_dict["train_labels"] = train_feats.cpu(), train_labels
        output_dict["id_data_feats"], output_dict["id_data_labels"] = src_feats.cpu(), src_labels
        output_dict["ood1_data_feats"], output_dict["ood1_data_labels"] = tar1_feats.cpu(), tar1_labels
        output_dict["ood2_data_feats"], output_dict["ood2_data_labels"] = tar2_feats.cpu(), tar2_labels
        torch.save(output_dict, save_feats)
        print(f"Features saved to {save_feats}")

    ################################################
    print("Euclidean distances in a non-normalized space:")
    # eucl distance in a non-normalized space
    src_dist, src_ids = knn(train_feats.unsqueeze(0), src_feats.unsqueeze(0))
    src_dist = src_dist.squeeze().cpu()
    src_ids = src_ids.squeeze().cpu()  # index of nearest training sample
    src_scores = 1 / src_dist
    src_pred = np.asarray([train_labels[i] for i in src_ids])  # pred is label of nearest training sample

    # OOD tar1
    tar1_dist, _ = knn(train_feats.unsqueeze(0), tar1_feats.unsqueeze(0))
    tar1_dist = tar1_dist.squeeze().cpu()
    tar1_scores = 1 / tar1_dist

    # OOD tar2
    tar2_dist, _ = knn(train_feats.unsqueeze(0), tar2_feats.unsqueeze(0))
    tar2_dist = tar2_dist.squeeze().cpu()
    tar2_scores = 1 / tar2_dist

    eval_ood_sncore(
        scores_list=[src_scores, tar1_scores, tar2_scores],
        preds_list=[src_pred, None, None],  # [src_pred, None, None],
        labels_list=[src_labels, None, None],  # [src_labels, None, None],
        src_label=1  # confidence should be higher for ID samples
    )

    print("\nEuclidean distances with prototypes:")
    # eucl distance in a non-normalized space
    src_dist, src_ids = knn(prototypes.unsqueeze(0), src_feats.unsqueeze(0))
    src_dist = src_dist.squeeze().cpu()
    src_ids = src_ids.squeeze().cpu()  # index of nearest training sample
    src_scores = 1 / src_dist
    src_pred = np.asarray([train_labels[i] for i in src_ids])  # pred is label of nearest training sample

    # OOD tar1
    tar1_dist, _ = knn(prototypes.unsqueeze(0), tar1_feats.unsqueeze(0))
    tar1_dist = tar1_dist.squeeze().cpu()
    tar1_scores = 1 / tar1_dist

    # OOD tar2
    tar2_dist, _ = knn(prototypes.unsqueeze(0), tar2_feats.unsqueeze(0))
    tar2_dist = tar2_dist.squeeze().cpu()
    tar2_scores = 1 / tar2_dist

    eval_ood_sncore(
        scores_list=[src_scores, tar1_scores, tar2_scores],
        preds_list=[src_pred, None, None],
        labels_list=[src_labels, None, None],
        src_label=1  # confidence should be higher for ID samples
    )

    ################################################
    print("\nCosine similarities on the hypersphere:")
    # cosine sim in a normalized space
    train_feats = F.normalize(train_feats, p=2, dim=1)
    src_feats = F.normalize(src_feats, p=2, dim=1)
    tar1_feats = F.normalize(tar1_feats, p=2, dim=1)
    tar2_feats = F.normalize(tar2_feats, p=2, dim=1)
    src_scores, src_ids = torch.mm(src_feats, train_feats.t()).max(1)
    tar1_scores, _ = torch.mm(tar1_feats, train_feats.t()).max(1)
    tar2_scores, _ = torch.mm(tar2_feats, train_feats.t()).max(1)
    src_pred = np.asarray([train_labels[i] for i in src_ids])  # pred is label of nearest training sample

    eval_ood_sncore(
        scores_list=[(0.5 * src_scores + 0.5).cpu(), (0.5 * tar1_scores + 0.5).cpu(), (0.5 * tar2_scores + 0.5).cpu()],
        preds_list=[src_pred, None, None],  # [src_pred, None, None],
        labels_list=[src_labels, None, None],  # [src_labels, None, None],
        src_label=1  # confidence should be higher for ID samples
    )
    print("\nCosine similarities with prototypes:")
    # cosine sim in a normalized space
    prototypes = F.normalize(prototypes, p=2, dim=1)
    src_feats = F.normalize(src_feats, p=2, dim=1)
    tar1_feats = F.normalize(tar1_feats, p=2, dim=1)
    tar2_feats = F.normalize(tar2_feats, p=2, dim=1)
    src_scores, src_ids = torch.mm(src_feats, prototypes.t()).max(1)
    tar1_scores, _ = torch.mm(tar1_feats, prototypes.t()).max(1)
    tar2_scores, _ = torch.mm(tar2_feats, prototypes.t()).max(1)
    src_pred = np.asarray([train_labels[i] for i in src_ids])  # pred is label of nearest training sample
    eval_ood_sncore(
        scores_list=[(0.5 * src_scores + 0.5).cpu(), (0.5 * tar1_scores + 0.5).cpu(), (0.5 * tar2_scores + 0.5).cpu()],
        preds_list=[src_pred, None, None],
        labels_list=[src_labels, None, None],
        src_label=1  # confidence should be higher for ID samples
    )
    print("#" * 80)


def get_list_corr_data(opt, severity=None, split="train"):
    assert split in ['train', 'test']

    if opt.src == "SR1":
        prefix = "modelnet_set1"
    elif opt.src == "SR2":
        prefix = "modelnet_set2"
    else:
        raise ValueError(f"Expected SR source but received: {opt.src} ")

    print(f"get_list_corr_data for {prefix} - split {split}")

    # loads corrupted data
    if severity is None:
        severity = [1, 2, 3, 4]
    if opt.corruption == 'lidar' or opt.corruption == 'occlusion':
        print(f"loading {opt.corruption} data")
        root = osp.join(opt.data_root, "ModelNet40_corrupted", opt.corruption)
        file_names = [f"{root}/{prefix}_{split}_{opt.corruption}_sev" + str(i) + ".h5" for i in severity]
        print(f"corr list files: {file_names}\n")
    elif opt.corruption == 'all':
        print("loading both lidar and occlusion data")
        file_names = []
        root_lidar = osp.join(opt.data_root, "ModelNet40_corrupted", "lidar")
        file_names.extend([f"{root_lidar}/{prefix}_{split}_lidar_sev" + str(i) + ".h5" for i in severity])
        root_occ = osp.join(opt.data_root, "ModelNet40_corrupted", "occlusion")
        file_names.extend([f"{root_occ}/{prefix}_{split}_occlusion_sev" + str(i) + ".h5" for i in severity])
        print(f"corr list files: {file_names}\n")
    else:
        raise ValueError(f"Unknown corruption specified: {opt.corruption}")

    # augmentation mgmt
    if opt.script_mode.startswith("eval"):
        augm_set = None
    else:
        # synth -> real augm
        warnings.warn(f"Using RW augmentation set for corrupted data")
        augm_set = transforms.Compose([
            PointcloudToTensor(),
            AugmScale(),
            AugmRotate(axis=[0.0, 1.0, 0.0]),
            AugmRotatePerturbation(),
            AugmTranslate(),
            AugmJitter()
        ])

    corrupted_datasets = []
    for h5_path in file_names:
        corrupted_datasets.append(H5_Dataset(h5_file=h5_path, num_points=opt.num_points, transforms=augm_set))

    return corrupted_datasets


### for evaluation routine ###
def get_md_eval_loaders(opt):
    assert opt.script_mode.startswith("eval")
    if not str(opt.src).startswith('SR'):
        raise ValueError(f"Unknown modelnet src: {opt.src}")

    train_data = ModelNet40_OOD(
        data_root=opt.data_root,
        train=True,
        num_points=opt.num_points,
        class_choice=opt.src,
        transforms=None)

    print(f"{opt.src} train data len: {len(train_data)}")

    # append corrupted data to train dataset
    if opt.corruption:
        l_corr_data = get_list_corr_data(opt)  # list of corrupted datasets
        assert isinstance(l_corr_data, list)
        assert isinstance(l_corr_data[0], data.Dataset)
        l_corr_data.append(train_data)  # appending clean data to list corrupted datasets
        train_data = torch.utils.data.ConcatDataset(l_corr_data)  # concat Dataset
        print(f"Cumulative (clean+corrupted) train data len: {len(train_data)}")

    # test data (only clean samples)
    test_data = ModelNet40_OOD(
        data_root=opt.data_root,
        train=False,
        num_points=opt.num_points,
        class_choice=opt.src,
        transforms=None)

    train_loader = DataLoader(train_data, batch_size=opt.batch_size, num_workers=opt.num_workers,
                              worker_init_fn=init_np_seed, shuffle=False, drop_last=False)
    test_loader = DataLoader(test_data, batch_size=opt.batch_size, num_workers=opt.num_workers,
                             worker_init_fn=init_np_seed, shuffle=False, drop_last=False)
    return train_loader, test_loader


def eval_ood_PointNet_CE_Euclidean_norm(opt, config):
    print(f"Arguments: {opt}")
    set_random_seed(opt.seed)

    dataloader_config = {
        'batch_size': opt.batch_size, 'drop_last': False, 'shuffle': False,
        'num_workers': opt.num_workers, 'sampler': None, 'worker_init_fn': init_np_seed}

    # whole evaluation is done on ScanObject RW data
    sonn_args = {
        'data_root': opt.data_root,
        'sonn_split': opt.sonn_split,
        'h5_file': opt.sonn_h5_name,
        'split': 'all',  # we use both training (unused) and test samples during evaluation
        'num_points': opt.num_points_test,  # default: use all 2048 sonn points to avoid sampling randomicity
        'transforms': None  # no augmentation applied at inference time
    }

    train_loader, _ = get_md_eval_loaders(opt)
    if opt.src == 'SR1':
        print("Src is SR1\n")
        id_loader = DataLoader(ScanObject(class_choice="sonn_2_mdSet1", **sonn_args), **dataloader_config)
        ood1_loader = DataLoader(ScanObject(class_choice="sonn_2_mdSet2", **sonn_args), **dataloader_config)
    elif opt.src == 'SR2':
        print("Src is SR2\n")
        id_loader = DataLoader(ScanObject(class_choice="sonn_2_mdSet2", **sonn_args), **dataloader_config)
        ood1_loader = DataLoader(ScanObject(class_choice="sonn_2_mdSet1", **sonn_args), **dataloader_config)
    else:
        raise ValueError(f"OOD evaluation - wrong src: {opt.src}")

    # second SONN out-of-distribution set is common to both SR1 and SR2 sources
    # these are the samples from SONN categories with poor mapping to ModelNet categories
    ood2_loader = DataLoader(ScanObject(class_choice="sonn_ood_common", **sonn_args), **dataloader_config)

    classes_dict = eval(opt.src)
    n_classes = len(set(classes_dict.values()))
    model = Classifier(args=DotConfig(config['model']), num_classes=n_classes, loss=opt.loss, cs=opt.cs)
    ckt_weights = torch.load(opt.ckpt_path, map_location='cpu')['model']
    ckt_weights = sanitize_model_dict(ckt_weights)
    ckt_weights = convert_model_state(ckt_weights, model.state_dict())
    print(f"Model params count: {count_parameters(model) / 1000000 :.4f} M")
    print("Load weights: ", model.load_state_dict(ckt_weights, strict=True))
    model = model.cuda().eval()

    src_logits, src_pred, src_labels = get_network_output(model, id_loader)
    tar1_logits, _, tar1_labels = get_network_output(model, ood1_loader)
    tar2_logits, _, tar2_labels = get_network_output(model, ood2_loader)

    # # MSP
    # print("\n" + "#" * 80)
    # print("Computing OOD metrics with MSP normality score...")
    # src_MSP_scores = F.softmax(src_logits, dim=1).max(1)[0] # Evaluerer output på in distribution
    # tar1_MSP_scores = F.softmax(tar1_logits, dim=1).max(1)[0] # Evaluerer output på out of distribution
    # tar2_MSP_scores = F.softmax(tar2_logits, dim=1).max(1)[0] # Evaluerer output på out of distribution
    
    # save_data_and_scores(id_loader, ood1_loader, ood2_loader, src_labels, tar1_labels, tar2_labels, src_MSP_scores, tar1_MSP_scores, tar2_MSP_scores, "PN2_cosine", "MSP", opt.src, opt.corruption)
    # eval_ood_sncore(
    #     scores_list=[src_MSP_scores, tar1_MSP_scores, tar2_MSP_scores],
    #     preds_list=[src_pred, None, None],  # computes also MSP accuracy on ID test set
    #     labels_list=[src_labels, None, None],  # computes also MSP accuracy on ID test set
    #     src_label=1)
    # print("#" * 80)



    # MLS
    print("\n" + "#" * 80)
    print("Computing OOD metrics with MLS normality score...")
    src_MLS_scores = src_logits.max(1)[0]
    tar1_MLS_scores = tar1_logits.max(1)[0]
    tar2_MLS_scores = tar2_logits.max(1)[0]
    save_data_and_scores(id_loader, ood1_loader, ood2_loader, src_labels, tar1_labels, tar2_labels, src_MLS_scores, tar1_MLS_scores, tar2_MLS_scores, "PN2_cosine", "MLS", opt.src, opt.corruption)

    eval_ood_sncore(
        scores_list=[src_MLS_scores, tar1_MLS_scores, tar2_MLS_scores],
        preds_list=[src_pred, None, None],  # computes also MSP accuracy on ID test set
        labels_list=[src_labels, None, None],  # computes also MSP accuracy on ID test set
        src_label=1)
    print("#" * 80)

    # # entropy
    # print("\n" + "#" * 80)
    # src_entropy_scores = 1 / logits_entropy_loss(src_logits)
    # tar1_entropy_scores = 1 / logits_entropy_loss(tar1_logits)
    # tar2_entropy_scores = 1 / logits_entropy_loss(tar2_logits)
    # print("Computing OOD metrics with entropy normality score...")
    # eval_ood_sncore(
    #     scores_list=[src_entropy_scores, tar1_entropy_scores, tar2_entropy_scores],
    #     preds_list=[src_pred, None, None],  # computes also MSP accuracy on ID test set
    #     labels_list=[src_labels, None, None],  # computes also MSP accuracy on ID test set
    #     src_label=1)
    # print("#" * 80)


    # # FEATURES EVALUATION
    # eval_OOD_with_feats(model, train_loader, id_loader, ood1_loader, ood2_loader, save_feats=opt.save_feats)

    # # ODIN
    # print("\n" + "#" * 80)
    # print("Computing OOD metrics with ODIN normality score...")
    # src_odin = iterate_data_odin(model, id_loader)
    # tar1_odin = iterate_data_odin(model, ood1_loader)
    # tar2_odin = iterate_data_odin(model, ood2_loader)
    # eval_ood_sncore(scores_list=[src_odin, tar1_odin, tar2_odin], src_label=1)
    # print("#" * 80)

    # # Energy
    # print("\n" + "#" * 80)
    # print("Computing OOD metrics with Energy normality score...")
    # src_energy = iterate_data_energy(model, id_loader)
    # tar1_energy = iterate_data_energy(model, ood1_loader)
    # tar2_energy = iterate_data_energy(model, ood2_loader)
    # eval_ood_sncore(scores_list=[src_energy, tar1_energy, tar2_energy], src_label=1)
    # print("#" * 80)

    # # GradNorm
    # print("\n" + "#" * 80)
    # print("Computing OOD metrics with GradNorm normality score...")
    # src_gradnorm = iterate_data_gradnorm(model, id_loader)
    # tar1_gradnorm = iterate_data_gradnorm(model, ood1_loader)
    # tar2_gradnorm = iterate_data_gradnorm(model, ood2_loader)
    # eval_ood_sncore(scores_list=[src_gradnorm, tar1_gradnorm, tar2_gradnorm], src_label=1)
    # print("#" * 80)

    # # React with id-dependent threshold
    # print("\n" + "#" * 80)
    # val_loader = get_md_react_val_loader(opt)
    # threshold = estimate_react_thres(model, val_loader)
    # print(f"Computing OOD metrics with React (+Energy) normality score, ID-dependent threshold (={threshold:.4f})...")
    # print(f"React - using {opt.src} test to compute threshold")
    # src_react = iterate_data_react(model, id_loader, threshold=threshold)
    # tar1_react = iterate_data_react(model, ood1_loader, threshold=threshold)
    # tar2_react = iterate_data_react(model, ood2_loader, threshold=threshold)
    # eval_ood_sncore(scores_list=[src_react, tar1_react, tar2_react], src_label=1)
    # print("#" * 80)
    return


def main():
    args = get_args()
    config = load_yaml(args.config)

    # eval Modelnet -> SONN
    assert args.ckpt_path is not None and len(args.ckpt_path)
    print("out-of-distribution eval - Modelnet -> SONN ..")
    eval_ood_PointNet_CE_Euclidean_norm(args, config)


if __name__ == '__main__':
    main()