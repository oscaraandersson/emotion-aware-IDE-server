import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
# from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import MinMaxScaler

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


class Model(nn.Module):
    def __init__(self):
        super(Model,self).__init__()
        self.fc1 = nn.Linear(19,19)
        self.fc2 = nn.Linear(19, 10)
        self.fc3 = nn.Linear(10, 4)

    def forward(self,x):
        x = torch.sigmoid(self.fc1(x))
        x = torch.sigmoid(self.fc2(x))
        x = torch.sigmoid(self.fc3(x))
        return x

def accuracy(y_pred, y_test):
    a = y_pred.argmax(1)
    m = torch.zeros(y_pred.shape).scatter(1, a.unsqueeze(1), 1.0)
    torch.equal(m, y_test), m.shape[0]
    total = y_test.shape[0]
    correct = 0

    for i in range(m.shape[0]):
        if torch.equal(m[i], y_test[i]):
            correct += 1
    correct
    return correct / total

# train = True
train = False

if train == True:
    arousal = pd.read_csv('data/SAM_arousal.csv')
    valence = pd.read_csv('data/SAM_valence.csv')

    X = arousal.iloc[:, 34:len(arousal.columns)-1].values
    arousal['valence'] = valence.iloc[:, -1]
    class_dict = {'high': 0, 'low': 1, 'positive': 2, 'negative': 3}
    arousal['target'] = arousal.apply(lambda x: f'{x.arousal}, {x.valence}', axis=1)
    y = pd.get_dummies(data=arousal.target).values

    x_train, x_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=1, stratify=y)

    #feature scaling
    sc = MinMaxScaler()
    x_train = sc.fit_transform(x_train)
    x_test = sc.transform(x_test)

    #training and testing tensors
    train_set = dataset(x_train,y_train)
    test_set = dataset(x_test,y_test)

    #some parameters
    model = Model()
    learning_rate = 0.01
    optimizer = torch.optim.Adam(model.parameters(),lr=learning_rate)
    epochs = 600
    criterion = nn.BCELoss()

    #data loader
    train_loader = DataLoader(train_set,shuffle=True,batch_size=train_set.__len__())
    test_loader = DataLoader(test_set,batch_size=test_set.__len__())

    #forward pass
    losses = []
    accuracies = []
    for i in range(epochs):
        for j,(x_train,y_train) in enumerate(train_loader):
            #get the prediction
            y_pred = model(x_train)

            #losses
            loss = criterion(y_pred,y_train)
            accuracies.append(accuracy(y_pred, y_train))
            losses.append(loss.detach().numpy())
            #backprop
            optimizer.zero_grad()

            loss.backward()
            optimizer.step()
        #print loss
        if i%50 == 0:
            print("epoch : {} loss: {}".format(i,loss))

    #testset
    x_test,y_test = next(iter(test_loader))
    y_pred = model(x_test)
    a = y_pred.argmax(1)
    m = torch.zeros(y_pred.shape).scatter(1, a.unsqueeze(1), 1.0)
    torch.equal(m, y_test), m.shape[0]
    total = y_test.shape[0]
    correct = 0

    for i in range(m.shape[0]):
        if torch.equal(m[i], y_test[i]):
            correct += 1

    print('accuracy of the model on test set : ', correct / total)

    # plot loss
    fig, ax = plt.subplots(2, 1)
    ax[0].plot(losses)
    ax[0].set_title('loss and accuracy vs epochs')
    ax[0].set_xlabel('epochs')
    ax[0].set_ylabel('loss')

    ax[1].plot(accuracies)
    ax[1].set_xlabel('epochs')
    ax[1].set_ylabel('accuracy')

    fig.show()

    save = input('Save model? y for yes: ')

    if save == 'y':
        torch.save(model.state_dict(), f'models/emotion_classifier.pth')

