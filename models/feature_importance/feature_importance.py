import os
from tqdm import tqdm
import pickle

from sklearn.metrics import f1_score
import numpy as np
import torch
from torch import nn
import pytorch_lightning as pl

from torch.utils.data import DataLoader
from copy import deepcopy
import src.predict as model_predict


# Define a function to calculate model precision_score
def estimate_metrics(y_probs, y_dict, sklearn_binary_metric):
    scores = {}
    for key in y_probs.keys():
        if (key == "lstm") or (key == "transformer") or (key == "conv_lstm"):
            scores[key] = sklearn_binary_metric(
                y_dict["lstm"].argmax(1), y_probs[key].argmax(1), average="macro"
            )
        else:
            scores[key] = sklearn_binary_metric(
                y_dict["mlp"].argmax(1), y_probs[key].argmax(1), average="macro"
            )
    return scores


def estimate_feature_importance_models(
    clf_dict,
    X_dict,
    y_dict,
    feature_names_dict,
    num_permutations,
    sklearn_binary_metric,
):
    # Initialize an array to store the feature importance scores
    # feature_names = feature_names_dict["mlp"] #keep this key for any case
    # Calculate original score
    print("Predicting on test data")
    y_probs = model_predict.make_predictions(X_dict, clf_dict)
    # y_probs["mean_ensemble_" + "_".join(list(y_probs.keys()))] = sum(
    #     list(y_probs.values())
    # ) / len(clf_dict)
    original_score = estimate_metrics(y_probs, y_dict, sklearn_binary_metric)
    # original_precision_score = calculate_precision_score(
    #     model, input_data, target_data, DataSet, sklearn_binary_metric
    # )
    feature_importance_scores = {
        model_name: {} for model_name in y_probs.keys()
        }
    

    # # Loop over each feature dimension
    # for feature_dim, feature_name in tqdm(enumerate(feature_names)):
    #     print(f"Calculating importance for feature {feature_names[feature_dim]}")

    #     # Loop over each permutation
    #     for i in range(num_permutations):
    #         # Create a copy of the input data for shuffling
    #         shuffled_input_data = deepcopy(X_dict)
    #         for k in shuffled_input_data.keys():
    #             if type(shuffled_input_data[k]) == np.ndarray:
    #                 # Shuffle the values of the current feature dimension
    #                 np.random.shuffle(shuffled_input_data[k][:, feature_dim])
    #             elif type(shuffled_input_data[k]) == tuple:
    #                 shuffled_input_data[k] = list(shuffled_input_data[k])
    #                 monthly_idx = np.where(
    #                     feature_names_dict["monthly"].flatten() == feature_name
    #                 )
    #                 static_idx = np.where(feature_names_dict["static"] == feature_name)
    #                 if len(monthly_idx[0]) != 0:
    #                     reshaped_m = shuffled_input_data[k][0].reshape(
    #                         shuffled_input_data[k][0].shape[0], -1
    #                     )
    #                     np.random.shuffle(reshaped_m[:, monthly_idx[0]])
    #                     shuffled_input_data[k][0] = reshaped_m.reshape(
    #                         shuffled_input_data[k][0].shape
    #                     )
    #                 if len(static_idx[0]) != 0:
    #                     np.random.shuffle(shuffled_input_data[k][1])

    #         # make prediction
    #         # for each model estimate chosen metric + ensemble metrics
    #         # add to list

    #         shuffled_preds = model_predict.make_predictions(
    #             shuffled_input_data, clf_dict
    #         )

    # # Loop over each feature dimension
    for model_name in clf_dict.keys():
        if model_name=="lstm" or model_name=="conv_lstm" or model_name=="transformer":
            feature_names = feature_names_dict["lstm"]
        else:
            feature_names = feature_names_dict["mlp"]
        
        feature_importance_scores[model_name] = {fn: [] for fn in feature_names}

        for feature_dim, feature_name in tqdm(enumerate(feature_names)):
            print(f"Calculating importance for feature {feature_name}")

            # Loop over each permutation
            for i in range(num_permutations):
                # Create a copy of the input data for shuffling
                shuffled_input_data = deepcopy(X_dict)

                if model_name=="lstm" or model_name=="conv_lstm" or model_name=="transformer":
                    np.random.shuffle(shuffled_input_data["lstm"][:, :, feature_dim])

                else:
                    np.random.shuffle(shuffled_input_data["mlp"][:, feature_dim])

                # make prediction
                shuffled_preds = model_predict.make_predictions(
                    shuffled_input_data, clf_dict
                )

                # for each model estimate chosen metric
                shuffled_score = estimate_metrics(
                    shuffled_preds, y_dict, sklearn_binary_metric
                )

                # Calculate the difference in accuracy between the shuffled and original input data
                importance_score = original_score[model_name] - shuffled_score[model_name] 

                del shuffled_input_data

                # Add the importance score to the array
                for model_name in original_score.keys():
                    feature_importance_scores[model_name][feature_name].append(
                        importance_score
                    )
            
    # Save
    for model in y_probs.keys():
        with open(
        "/ArableLandSuitability/results/feature_importance/feature_importance_{}.pkl".format(model), "wb"
    ) as fs:
            pickle.dump(feature_importance_scores[model], fs)

    # return feature_importance_scores