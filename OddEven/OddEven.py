import torch, matplotlib.pyplot as plt
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from random import randint, seed

# This is a simple machine learning experiment
# Given a 3-input sample including a random value
#     will the network ignore the random value?
# Based on several runs, the random value is not ignored and full training is not achieved

seed(123) # repeatable
torch.manual_seed(0) # repeatable

def BuildTensors():
    lstx = []
    lsty = []
    for i in range(100): # 0-99, 100 samples
        # --- X samples ---
        # 3 inputs: random number, index, odd\even
        lstx.append([float(randint(0, 1000)), float(i), float(i%2)])
        # 3 inputs: all odd\even flag
        # lstx.append([float(i%2), float(i%3), float(i%2)])
        # 3 inputs: constant, index, odd\even flag
        # lstx.append([0.0, float(i), float(i%2)])

        # --- Y outputs ---
        lsty.append(float(i%2)) # odd\even
    return torch.tensor(lstx), torch.tensor(lsty)

class Data(Dataset):
    def __init__(self):
        self.x, self.y = BuildTensors()
        self.y = self.y.view(-1, 1)
        self.len = self.x.shape[0]

    def __getitem__(self, index):
        return self.x[index], self.y[index]

    def __len__(self):
        return self.len

class Net(nn.Module): # model class
    def __init__(self, D_in, H, D_out): # neuron counts - input\hidden\output
        super(Net, self).__init__()
        self.linear1 = nn.Linear(D_in, H) # input\hidden
        self.linear2 = nn.Linear(H, D_out) # hidden\output

    def forward(self, x):
        x = torch.sigmoid(self.linear1(x)) # all neurons input layer
        x = torch.sigmoid(self.linear2(x)) # all neurons hidden layer
        return x

def train(data_set, model, criterion, train_loader, optimizer, epochs=5, plot_number=10):
    cost = []
    for epoch in range(epochs):
        total = 0
        for x, y in train_loader:
            optimizer.zero_grad() # reset gradient
            yhat = model(x) # prediction
            loss = criterion(yhat, y) # bce loss
            optimizer.zero_grad() # reset gradient
            loss.backward() # derivative
            optimizer.step() # take step
            total += loss.item()

        cost.append(total)
    plt.figure()
    plt.plot(cost)
    plt.xlabel('epoch')
    plt.ylabel('cost')
    plt.show()
    return cost

data_set=Data() # new dataset

model=Net(3,9,1) # 3 input neurons, 9 neurons in hidden layer
learning_rate=0.1
criterion=nn.BCELoss() # binary cross entropy
optimizer=torch.optim.Adam(model.parameters(), lr=learning_rate)
train_loader=DataLoader(dataset=data_set, batch_size=100)
cost=train(data_set,model,criterion, train_loader, optimizer, epochs=100, plot_number=50)

plt.plot(cost)
