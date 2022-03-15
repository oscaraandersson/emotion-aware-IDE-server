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

data = 'valence'
# data = 'arousal'

if data == 'arousal':
    df = pd.read_csv('data/SAM_arousal.csv')
    class_dict = {'high': 1, 'low': 0}
else:
    df = pd.read_csv('data/SAM_valence.csv')
    class_dict = {'positive': 1, 'negative': 0}

X = df.iloc[:, 34:len(df.columns)-1].values
y = df.iloc[:, -1].map(class_dict).values

x_train, x_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=1, stratify=y)

#feature scaling
sc = StandardScaler()
x_train = sc.fit_transform(x_train)
x_test = sc.transform(x_test)

#dataset class
class dataset(Dataset):
    def __init__(self,x,y):
        self.x = torch.tensor(x,dtype=torch.float32)
        self.y = torch.tensor(y,dtype=torch.float32)
        self.length = self.x.shape[0]

    def __getitem__(self,idx):
        return self.x[idx],self.y[idx]
    def __len__(self):
        return self.length


#training and testing tensors
train_set = dataset(x_train,y_train)
test_set = dataset(x_test,y_test)

#defining the network
class Model(nn.Module):
    def __init__(self):
        super(Model,self).__init__()
        self.fc1 = nn.Linear(19,1)

    def forward(self,x):
        x = torch.sigmoid(self.fc1(x))
        return x


#some parameters
model = Model()
learning_rate = 0.01
optimizer = torch.optim.Adam(model.parameters(),lr=learning_rate)
epochs = 1500
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
save = input('Save model? y for yes: ')

if save == 'y':
    torch.save(model.state_dict(), f'models/{data}.pth')

