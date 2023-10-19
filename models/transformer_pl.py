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
    CroplandDatasetTest,
    CroplandDataModuleLSTM,
    CropTransformer,
    CropPL,
)
from pytorch_lightning.callbacks import (
    LearningRateMonitor,
    ModelCheckpoint,
    RichProgressBar,
)
from pytorch_lightning.callbacks.early_stopping import EarlyStopping
from torch import nn
from torch.utils.data import DataLoader


### Read from file
# Read dictionary pkl file
with open(
    os.path.join("..", "data", "processed_files", "pkls", "X_lstm.pkl"), "rb"
) as fp:
    X = pickle.load(fp)

with open(
    os.path.join("..", "data", "processed_files", "pkls", "y_lstm.pkl"), "rb"
) as fp:
    y = pickle.load(fp)

# initilize data module
dm = CroplandDataModuleLSTM(X=X, y=y, batch_size=16384, num_workers=0)

# initilize model
warnings.filterwarnings("ignore")
torch.manual_seed(42)
random.seed(42)

network = CropTransformer()
model = CropPL(net=network, lr=5e-4, weight=None)

# initilize trainer
early_stop_callback = EarlyStopping(
    monitor="val/F1Score", min_delta=1e-3, patience=50, verbose=True, mode="max"
)
model_saving = ModelCheckpoint(save_top_k=3, mode="max", monitor="val/F1Score")
lr_monitor = LearningRateMonitor(logging_interval="epoch")

trainer = pl.Trainer(
    max_epochs=500,
    accelerator="gpu",
    devices=[3],
    check_val_every_n_epoch=1,
    callbacks=[early_stop_callback, model_saving, lr_monitor, RichProgressBar()],
)
trainer.fit(model, dm)


# Save the module to a file
model_filename = os.path.join("..", "results", "pickle_models", "transformer.pkl")
torch.save(model, model_filename)

# check metrics
predictions = torch.cat(
    trainer.predict(
        model,
        DataLoader(
            CroplandDatasetTest((dm.X_monthly_test, dm.X_static_test)), batch_size=2048
        ),
    ),
    dim=0,
)
softmax = nn.Softmax(dim=1)
yprob = softmax(predictions.float())
ypred = torch.argmax(yprob, 1)
ytest = torch.argmax(dm.y_test, 1).cpu().numpy()


custom_multiclass_report(ytest, ypred, yprob)
