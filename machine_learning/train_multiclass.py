import pandas as pd
import numpy as np
import copy
import os
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.model_selection import KFold 
from sklearn.model_selection import StratifiedKFold 
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
    correct
    return correct / total

# train = True
train = False

if train == True:
    # Arousal and valence has the same data but different labels
    arousal = pd.read_csv('data/SAM_arousal.csv')
    valence = pd.read_csv('data/SAM_valence.csv')

    X = arousal.iloc[:, 34:len(arousal.columns)-1].values
    arousal['valence'] = valence.iloc[:, -1]
    class_dict = {'high': 0, 'low': 1, 'positive': 2, 'negative': 3}

    # Converting the binary classes for valence and arousal to 4 classes
    # There are combinations of 2 binary classes
    arousal['target'] = arousal.apply(lambda x: f'{x.arousal}, {x.valence}', axis=1)
    y = pd.get_dummies(data=arousal.target).values


    #feature scaling
    #sc = MinMaxScaler()
    sc = StandardScaler()
    X = sc.fit_transform(X)
    dump(sc, 'scaler.joblib')
    X_train, X_test, Y_train, Y_test = train_test_split(X, y, test_size=0.1, random_state=1, stratify=y)
    data_set = dataset(X_train, Y_train)

    best_model = None
    best_acc = 0

    #some parameters
    learning_rate = 0.01
    epochs = 400
    criterion = nn.BCELoss()
    k = 10
    splits = StratifiedKFold(n_splits=k, shuffle=True, random_state=42)
    accuracies = []

    for fold, (train_idx, val_idx) in enumerate(splits.split(X_train, Y_train.argmax(1))):
        #data loader
        train_sampler = SubsetRandomSampler(train_idx)
        test_sampler = SubsetRandomSampler(val_idx)
        train_loader = DataLoader(data_set,batch_size=data_set.__len__(), sampler=train_sampler)
        test_loader = DataLoader(data_set,batch_size=data_set.__len__(),sampler=test_sampler)

        model = Model()
        optimizer = torch.optim.Adam(model.parameters(),lr=learning_rate)

        #forward pass
        losses = []
        fold_accuracies = []
        
        for i in range(epochs):
            for j,(x_train,y_train) in enumerate(train_loader):
                #get the prediction
                y_pred = model(x_train)

                #losses
                loss = criterion(y_pred,y_train)
                acc = accuracy(y_pred, y_train)
                fold_accuracies.append(acc)
                losses.append(loss.detach().numpy())
                #backprop
                optimizer.zero_grad()

                loss.backward()
                optimizer.step()

        x_test,y_test = next(iter(test_loader))
        y_pred = model(x_test)
        a = y_pred.argmax(1)
        m = torch.zeros(y_pred.shape).scatter(1, a.unsqueeze(1), 1.0)
        #torch.equal(m, y_test), m.shape[0]
        total = y_test.shape[0]
        correct = 0

        for i in range(m.shape[0]):
            if torch.equal(m[i], y_test[i]):
                correct += 1

        acc = correct/total
        if acc > best_acc:
            best_model = copy.deepcopy(model)
        accuracies.append(correct/total)
        print('Fold: ', fold + 1, ': accuracy of the model on test set : ', correct / total)

    avg_acc = sum(accuracies)/len(accuracies)
    print(f'The average accuracy is: {avg_acc}')

    test_set = dataset(X_test, Y_test)
    test_loader = DataLoader(test_set, batch_size=data_set.__len__())
    x_test, y_test = next(iter(test_loader))
    y_pred = model(x_test)
    a = y_pred.argmax(1)
    m = torch.zeros(y_pred.shape).scatter(1, a.unsqueeze(1), 1.0)
    from sklearn.metrics import multilabel_confusion_matrix
    from sklearn.metrics import classification_report
    print(multilabel_confusion_matrix(y_test, m))
    print(classification_report(y_test, m))
    # plot loss
    fig, ax = plt.subplots(2, 1)
    ax[0].plot(losses)
    ax[0].set_title('loss and accuracy vs epochs')
    ax[0].set_xlabel('epochs')
    ax[0].set_ylabel('loss')

    ax[1].plot(fold_accuracies)
    ax[1].set_xlabel('epochs')
    ax[1].set_ylabel('accuracy')

    fig.show()

    save = input('Save model? y for yes: ')

    if save == 'y':
        torch.save(model.state_dict(), f'models/emotion_classifier.pth')

