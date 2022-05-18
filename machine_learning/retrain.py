import pandas as pd
import numpy as np
import copy
import os
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import MinMaxScaler
from joblib import dump

import torch
from torch import nn
from torch.nn import functional as F
from torch.utils.data import Dataset, DataLoader, SubsetRandomSampler

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
    return correct / total

def label_to_onehot(lst):
    labels = []
    for label in lst:
        temp = [0, 0, 0, 0]
        temp[int(label)-1] = 1
        labels.append(temp)
    return np.array(labels)

def train(new_df):
    # Arousal and valence has the same data but different labels
    arousal = pd.read_csv('data/SAM_arousal.csv')
    valence = pd.read_csv('data/SAM_valence.csv')

    X = arousal.iloc[:, 34:len(arousal.columns) - 1].values
    arousal['valence'] = valence.iloc[:, -1]
    class_dict = {
        'high, negative': 1,
        'high, positive': 2,
        'low, negative': 3,
        'low, positive': 4
    }

    # Converting the binary classes for valence and arousal to 4 classes
    # There are 4 combinations of 2 binary classes
    arousal['target'] = arousal.apply(lambda x: f'{x.arousal}, {x.valence}',
                                      axis=1)
    y = label_to_onehot(arousal.target.map(class_dict).to_list())

    new_df = new_df[new_df['label']!=0]

    y_new = label_to_onehot(new_df.label.to_list())
    X_new = new_df.drop(columns='label').to_numpy()

    X = np.concatenate((X,X_new))
    y = np.concatenate((y, y_new))

    sc = StandardScaler()
    X = sc.fit_transform(X)
    x_train, x_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=1, stratify=y)
    train_set = dataset(x_train, y_train)
    test_set = dataset(x_test, y_test)
    train_loader = DataLoader(train_set, batch_size=len(train_set))
    test_loader = DataLoader(test_set, batch_size=len(test_set))

    #some parameters
    learning_rate = 0.01
    epochs = 400
    criterion = nn.BCELoss()
    model = Model()
    optimizer = torch.optim.Adam(model.parameters(),lr=learning_rate)

    #forward pass
    train_loss = []
    train_accuracy = []
    
    for i in range(epochs):
        #get the prediction
        x_train, y_train = next(iter(train_loader))
        y_pred = model(x_train)

        loss = criterion(y_pred,y_train)
        acc = accuracy(y_pred, y_train)
        train_accuracy.append(acc)
        train_loss.append(loss.detach().numpy())
        #backprop
        optimizer.zero_grad()

        loss.backward()
        optimizer.step()

    x_test,y_test = next(iter(test_loader))
    y_pred = model(x_test)
    acc = accuracy(y_pred, y_test)
    print(acc)

    # Plotitng training loss and accuracy
    fig, ax = plt.subplots(2, 1)
    ax[0].plot(train_loss)
    ax[0].set_title('loss and accuracy vs epochs')
    ax[0].set_xlabel('epochs')
    ax[0].set_ylabel('loss')

    ax[1].plot(train_accuracy)
    ax[1].set_xlabel('epochs')
    ax[1].set_ylabel('accuracy')

    fig.show()

    save = input('Save model? y for yes: ')

    if save == 'y':
        dump(sc, 'scaler.joblib')
        torch.save(model.state_dict(), f'models/emotion_classifier.pth')
