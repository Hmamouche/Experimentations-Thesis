#!/usr/local/bin/python
# -*- coding: utf-8 -*-

# Author: Youssef Hmamouche

#from __future__ import print_function
#from sklearn.metrics import mean_squared_error
#from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import LSTM, Dense
from math import sqrt


import numpy as np
import pandas as pd
#import pprint

#import os



#------------------------------#
#-----+     COLORS      +------#
#------------------------------#
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

#-------------------------------------------------------------#
#----+     TRANSFORM THE DATA TO SUPPERISED STRUCTURE  +------#
#-------------------------------------------------------------#
class toSuppervisedData:
    targets = np.empty([0,0],dtype=float)
    data = np.empty([0,0],dtype=float)
    
    ## constructor
    def __init__(self, X, p):
        self.targets = self.targets_decomposition (X,p)
        self.data = self.matrix_decomposition (X,p)
    
    ## p-decomposition of a vector
    def vector_decomposition (self,x,p):
        n = len(x)
        output = np.empty([n-p,p],dtype=float)
        for i in range (n-p):
            for j in range (p):
                output[i,j] = x[i+j]
        return output

    ## p-decomposition of a target
    def target_decomposition (self,x,p):
        n = len(x)
        output = np.empty([n-p,1],dtype=float)
        for i in range (n-p):
            output[i] = x[i+p]
        return output

    ## p-decomposition of a matrix
    def matrix_decomposition (self,x,p):
        output = np.empty([0,0],dtype=float)
        out = np.empty([0,0],dtype=float)
        for i in range(x.shape[1]):
            out = self.vector_decomposition(x[:,i],p)
            #print (out)
            if output.size == 0:
                output = out
            else:
                output = np.concatenate ((output,out),axis=1)
        
        return output

    # extract all the targets decomposed
    def targets_decomposition (self,x,p):
        output = np.empty([0,0],dtype=float)
        out = np.empty([0,0],dtype=float)
        for i in range(x.shape[1]):
            out = self.target_decomposition(x[:,i],p)
            if output.size == 0:
                output = out
            else:
                output = np.concatenate ((output,out),axis=1)

        return output
#--------------------------------#
#----+     NORMALIZE      +------#
#--------------------------------#
def normalize (M):
    minMax = np.empty ([M.shape[1], 2])
    for i in range(M.shape[1]):
        #print (M[:,i])
        max = np.max(M[:,i])
        min = np.min(M[:,i])
        minMax[i,0] = min
        minMax[i,1] = max

        for j in range(M.shape[0]):
            M[j,i] = (M[j,i] - min) / (max - min)

    return minMax

#--------------------------------------#
#----+     DENORMALIZATION      +------#
#--------------------------------------#
def inverse_normalize (M,minMax):
    for i in range(M.shape[0]):
        M[i] = M[i] * (minMax[1] - minMax[0]) + minMax[0]
    return M

#------------------------------------------#
#----+     fit an LSTM network      +------#
#------------------------------------------#
def fit_lstm (train, look_back, batch_size, nb_epoch, neurons):
    X, y = train[:, 1:train.shape[1]], train[:, 0]
    X = X.reshape(X.shape[0], look_back, X.shape[1] / look_back)
    
    model = Sequential()
    model.add (LSTM (neurons, batch_input_shape = (batch_size, X.shape[1], X.shape[2])))
    model.add(Dense(1))
    
    model.compile(loss='mean_squared_error', optimizer='adam')
    
    for i in range(nb_epoch):
        model.fit(X, y, epochs=1, batch_size=batch_size, verbose=1, shuffle=False)
        model.reset_states()
    return model

#--------------------------------------------------------------#
#------------+     Make a One-Step Forecast       +------------#
#--------------------------------------------------------------#
def forecast_lstm (model,look_back, batchSize, X):
    X = X.reshape(X.shape[0], look_back, X.shape[1] / look_back)
    yhat = model.predict (X,  batch_size = batchSize)
    
    #print (yhat)
    #print (yhat[0, 0])
    return yhat[0, 0]

#-----------------------------------------#
#------------+     LSTM      +------------#
#-----------------------------------------#
def imp_LSTM (data, nbre_preds, p, nbre_iterations, neurons, batchSize = 1):

    # normalize the data
    minMax = normalize(data)

    # transform the data to supervised learning
    model = toSuppervisedData(data,p)
    X = model.data
    
    # Extract target variables
    targets = model.targets
    predictions = np.empty ([nbre_preds, 1])
    reals = targets[targets.shape[0] - nbre_preds:targets.shape[0],:]
    X = np.concatenate ((targets[:,0:1], X), axis = 1)
    limit = X.shape[0] - nbre_preds
    
    # Use 2 mini-batchs
    #if (limit % 2 == 1):
    #	train, test = X[1:limit], X[limit:X.shape[0]]
    #	batchSize = (limit - 1) / 2
    #else:
    #	train, test = X[0:limit], X[limit:X.shape[0]]
    #	batchSize = limit / 2
    #	batchSize = 1

    train, test = X[0:limit], X[limit:X.shape[0]]
    batchSize = 1    
    #batchSize = 1
    lstm_model =  fit_lstm(train, p, batchSize, nbre_iterations, neurons)
    prediction = []
    
    for j in range (0, nbre_preds):
        limit = X.shape[0] - nbre_preds + j
        test = X [limit - batchSize + 1  :limit+1]
        Xx, yy = test [:, 1:test.shape [1]], test[:, 0]
        #print (Xx. shape)
            
        # prediction
        yhat = forecast_lstm (lstm_model, p, batchSize, Xx)
        prediction.append (yhat)
    
        # update the model: online learning
        X_update = X[limit - batchSize + 1:limit+1]
        Xx, yy = X_update[:, 1:X.shape[1]], X_update[:, 0]
        Xx = Xx.reshape(Xx.shape[0], p, Xx.shape[1] / p)

        lstm_model.fit(Xx, yy, epochs=1, batch_size= batchSize, verbose = 0)    
    
    predictions[:,0] = prediction
    predictions = inverse_normalize (predictions,minMax[0,:])
    reals = inverse_normalize (reals, minMax[0,:])

    return predictions


#------------+      MAIN     +------------#
                                  
if __name__ == "__main__":
    print ("Hello spark")
