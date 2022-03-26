import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

import torch
from torch import nn
from torch.nn import functional as F
from torch.utils.data import Dataset
from torch.utils.data import DataLoader

class dataset(Dataset):
    def __init__(self,x,y):
        self.x = torch.tensor(x,dtype=torch.float32)
        self.y = torch.tensor(y,dtype=torch.float32)
        self.length = self.x.shape[0]

    def __getitem__(self,idx):
        return self.x[idx],self.y[idx]

    def __len__(self):
        return self.length


class ArousalModel(nn.Module):
    def __init__(self):
        super(ArousalModel,self).__init__()
        self.fc1 = nn.Linear(19,2)
        self.fc2 = nn.Linear(2, 1)

    def forward(self,x):
        x = torch.sigmoid(self.fc1(x))
        x = torch.sigmoid(self.fc2(x))
        return x

# train = True
train = False

if train == True:
    data = 'arousal'

    df = pd.read_csv('data/SAM_arousal.csv')
    class_dict = {'high': 1, 'low': 0}

    X = df.iloc[:, 34:len(df.columns)-1].values
    y = df.iloc[:, -1].map(class_dict).values

    x_train, x_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=1, stratify=y)

    #feature scaling
    sc = StandardScaler()
    x_train = sc.fit_transform(x_train)
    x_test = sc.transform(x_test)

    #training and testing tensors
    train_set = dataset(x_train,y_train)
    test_set = dataset(x_test,y_test)

    #some parameters
    model = Model()
    learning_rate = 0.01
    optimizer = torch.optim.Adam(model.parameters(),lr=learning_rate)
    epochs = 10000
    criterion = nn.BCELoss()

    #data loader
    train_loader = DataLoader(train_set,shuffle=True,batch_size=train_set.__len__())
    test_loader = DataLoader(test_set,batch_size=test_set.__len__())

    #forward pass
    losses = []
    for i in range(epochs):
        for j,(x_train,y_train) in enumerate(train_loader):
            #get the prediction
            y_pred = model(x_train)

            #losses
            loss = criterion(y_pred,y_train.reshape(-1,1))
            losses.append(loss.detach().numpy())
            #backprop
            optimizer.zero_grad()

            loss.backward()
            optimizer.step()
        #print loss
        if i%100 == 0:
            print("epoch : {} loss: {}".format(i,loss))

    #testset
    x_test,y_test = next(iter(test_loader))
    y_pred = model(x_test)
    n_correct_predictions = ((y_pred.round().reshape(-1) == y_test).sum())
    total_predictions = float(y_pred.shape[0])
    print('accuracy of the model on test set :', n_correct_predictions / total_predictions)

    # plot loss
    fig = plt.figure(figsize=(9, 5))
    ax = fig.add_subplot()
    ax.plot(losses)
    ax.set_title('loss vs epochs')
    ax.set_xlabel('epochs')
    ax.set_ylabel('loss')

    fig.show()

    save = input('Save model? y for yes: ')

    if save == 'y':
        torch.save(model.state_dict(), f'models/{data}.pth')

