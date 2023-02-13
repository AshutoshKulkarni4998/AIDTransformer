
import numpy as np
import os,sys,math
import argparse
from tqdm import tqdm
from einops import rearrange, repeat
import torch.nn as nn
import torch
from torch.utils.data import DataLoader
import torch.nn.functional as F
from ptflops import get_model_complexity_info
import time
import scipy.io as sio
from utils.loader import get_validation_data
import utils
from model import Network
from skimage import img_as_float32, img_as_ubyte
from ptflops import get_model_complexity_info
from thop import profile

parser = argparse.ArgumentParser(description='TESTING CODE FOR PAPER ID 0452')
parser.add_argument('--dataset',
    type=str, help='Mention the dataset to be tested: RICE Sate1K_Thin Sate1K_Moderate Sate1K_Thick')

parser.add_argument('--gpus', default='0', type=str, help='CUDA_VISIBLE_DEVICES')
parser.add_argument('--arch', default='Network', type=str, help='arch')
parser.add_argument('--batch_size', default=1, type=int, help='Batch size for dataloader')
parser.add_argument('--save_images', action='store_true', help='Save dehazed images in result directory')
parser.add_argument('--embed_dim', type=int, default=16, help='number of data loading workers')    
parser.add_argument('--win_size', type=int, default=8, help='number of data loading workers')
parser.add_argument('--token_projection', type=str,default='conv', help='linear/conv token projection')
parser.add_argument('--token_mlp', type=str,default='leff', help='ffn/leff token mlp')
# args for vit
parser.add_argument('--vit_dim', type=int, default=256, help='vit hidden_dim')
parser.add_argument('--vit_depth', type=int, default=12, help='vit depth')
parser.add_argument('--vit_nheads', type=int, default=8, help='vit hidden_dim')
parser.add_argument('--vit_mlp_dim', type=int, default=512, help='vit mlp_dim')
parser.add_argument('--vit_patch_size', type=int, default=16, help='vit patch_size')
parser.add_argument('--global_skip', action='store_true', default=False, help='global skip connection')
parser.add_argument('--local_skip', action='store_true', default=False, help='local skip connection')
parser.add_argument('--vit_share', action='store_true', default=False, help='share vit module')

args = parser.parse_args()


os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
os.environ["CUDA_VISIBLE_DEVICES"] = args.gpus

if args.dataset == 'RICE':
    input_dir = './testing_data/RICE/'
    result_dir = './results/Dehazed/RICE'
    checkpoint_dir = './checkpoints/RICE/RICE.pth'
elif args.dataset == 'Sate1K_Thin':
    input_dir = './testing_data/Sate1K/Thin/'
    result_dir = './results/Dehazed/Sate1K_Thin'
    checkpoint_dir = './checkpoints/Thin/Sate1K_Thin.pth'
elif args.dataset == 'Sate1K_Moderate':
    input_dir = './testing_data/Sate1K/Moderate/'
    result_dir = './results/Dehazed/Sate1K_Moderate'
    checkpoint_dir = './checkpoints/Moderate/Sate1K_Moderate.pth'
elif args.dataset == 'Sate1K_Thick':
    input_dir = './testing_data/Sate1K/Thick/'
    result_dir = './results/Dehazed/Sate1K_Thick'
    checkpoint_dir = './checkpoints/Thick/Sate1K_Thick.pth'
else:
    print("Please Mention the dataset to be tested: RICE Sate1K_Thin Sate1K_Moderate Sate1K_Thick")
    exit(0)
       

utils.mkdir(result_dir)

test_dataset = get_validation_data(input_dir)
test_loader = DataLoader(dataset=test_dataset, batch_size=1, shuffle=False, num_workers=0, drop_last=False)

model_restoration= utils.get_arch(args)
utils.load_checkpoint(model_restoration,checkpoint_dir)
print("=======================>Testing on {0} dataset<=======================".format(args.dataset))
model_restoration.cuda()
model_restoration.eval()
def expand2square(timg,factor=16.0):
    _, _, h, w = timg.size()

    X = int(math.ceil(max(h,w)/float(factor))*factor)

    img = torch.zeros(1,3,X,X).type_as(timg) # 3, h,w
    mask = torch.zeros(1,1,X,X).type_as(timg)

    
    img[:,:, ((X - h)//2):((X - h)//2 + h),((X - w)//2):((X - w)//2 + w)] = timg
    mask[:,:, ((X - h)//2):((X - h)//2 + h),((X - w)//2):((X - w)//2 + w)].fill_(1.0)
    
    return img, mask
with torch.no_grad():
    psnr_val_rgb = []
    ssim_val_rgb = []
    for ii, data_test in enumerate(tqdm(test_loader), 0):
        rgb_gt = data_test[0].numpy().squeeze().transpose((1,2,0))
        
        rgb_noisy, mask = expand2square(data_test[1].cuda(), factor=128) 
        filenames = data_test[2]
        
        rgb_restored = model_restoration(rgb_noisy, 1 - mask)
        rgb_restored = torch.masked_select(rgb_restored,mask.bool()).reshape(1,3,rgb_gt.shape[0],rgb_gt.shape[1])
        rgb_restored = torch.clamp(rgb_restored,0,1).cpu().numpy().squeeze().transpose((1,2,0))
        utils.save_img(os.path.join(result_dir,filenames[0]), img_as_ubyte(rgb_restored))

