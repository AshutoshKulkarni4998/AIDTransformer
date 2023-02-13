==========================================================================
Requirements:
python==3.9.6
torch==1.11.0
torchvision==0.12.0
matplotlib
scikit-image
opencv-python
yacs
joblib 
natsort 
h5py 
tqdm
einops
linformer
timm
ptflops
dataclasses
==========================================================================
For testing the code:
- Please run "python test.py --dataset [Put dataset name here]"
The dataset names are: RICE||Sate1K_Thin||Sate1K_Moderate||Sate1K_Thick
- The results will be stored in './results/Dehazed/[Dataset Name]/' folder
- Sample testing data is available in './testing_data/' folder
==========================================================================
