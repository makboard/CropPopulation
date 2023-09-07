# %%
import os
import pickle
import random
import sys
import warnings

sys.path.append(os.path.join(".."))

import pytorch_lightning as pl
import torch
from src.model_utils import (
    custom_multiclass_report,
    CroplandDataModule_LSTM,
    Crop_LSTM,
    Crop_PL,
)
from pytorch_lightning.callbacks import LearningRateMonitor
from pytorch_lightning.callbacks.early_stopping import EarlyStopping
from torch import nn
from torch.utils.data import DataLoader

torch.set_float32_matmul_precision("medium")

# %% [markdown]
# ### Read from file

# %%
# Read dictionary pkl file
with open(os.path.join("..", "data", "processed_files", "pkls", "X_FR_RUS_ROS_lstm.pkl"), "rb") as fp:
    X = pickle.load(fp)

with open(os.path.join("..", "data", "processed_files", "pkls", "y_FR_RUS_ROS_lstm.pkl"), "rb") as fp:
    y = pickle.load(fp)


# %%
# initilize data module
dm = CroplandDataModule_LSTM(X=X, y=y, batch_size=1024)

# initilize model
warnings.filterwarnings("ignore")
torch.manual_seed(142)
random.seed(142)

network = Crop_LSTM()
model = Crop_PL(net=network, lr=1e-3)

# initilize trainer
early_stop_callback = EarlyStopping(
    monitor="val/F1Score", min_delta=1e-3, patience=30, verbose=True, mode="max"
)
lr_monitor = LearningRateMonitor(logging_interval="epoch")

trainer = pl.Trainer(
    max_epochs=500,
    accelerator="gpu",
    # devices=[3],
    check_val_every_n_epoch=1,
    callbacks=[early_stop_callback, lr_monitor, pl.callbacks.RichProgressBar()],
)
trainer.fit(model, dm)


# %%
# from model_utils import custom_multiclass_report

# # check metrics
# predictions = torch.cat(
#     trainer.predict(model, DataLoader(dm.X_test, batch_size=128)), dim=0
# )
# softmax = nn.Softmax(dim=1)
# yprob = softmax(predictions.float())
# ypred = torch.argmax(yprob, 1)
# ytest = torch.argmax(dm.y_test, 1).cpu().numpy()


# print(custom_multiclass_report(ytest, ypred, yprob))

# %%
# Save the module to a file
model_filename = os.path.join("..", "results", "pickle_models", "lstm_FR_RUS_ROS.pkl")
torch.save(model, model_filename)