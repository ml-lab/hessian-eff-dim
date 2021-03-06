import math
import torch
import hess
import hess.utils as utils
import hess.nets
import numpy as np
import pickle

import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision
import torchvision.transforms as transforms

from compute_loss_surface import get_loss_surface
from hess.utils import get_hessian_eigs
from hess.nets import BasicConv as Net
import matplotlib.pyplot as plt
from gpytorch.utils.lanczos import lanczos_tridiag, lanczos_tridiag_to_diag

def main():
    use_cuda =  torch.cuda.is_available()

    model = Net()
    criterion = torch.nn.CrossEntropyLoss()

    if use_cuda:
        model = model.cuda()

    transform = transforms.Compose(
            [transforms.ToTensor(),
             transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))])

    trainset = torchvision.datasets.CIFAR10(root='/datasets/cifar10/', train=True,
                                            download=True, transform=transform)
    trainloader = torch.utils.data.DataLoader(trainset, batch_size=128,
                                              shuffle=True, num_workers=2)


    ## Super Trainer ##
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    for epoch in range(30):  # loop over the dataset multiple times

        running_loss = 0.0
        for i, data in enumerate(trainloader, 0):
            # get the inputs; data is a list of [inputs, labels]
            inputs, labels = data

            if use_cuda:
                inputs, labels = inputs.cuda(), labels.cuda()

            # zero the parameter gradients
            optimizer.zero_grad()

            # forward + backward + optimize
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            # print statistics
            running_loss += loss.item()
            if i % 100 == 99:    # print every 2000 mini-batches
                print('[%d, %5d] loss: %.3f' %
                      (epoch + 1, i + 1, running_loss / 100))
                running_loss = 0.0

    fpath = "./outputs/"
    fname = "saved_model.pt"
    torch.save(model.state_dict(), fpath + fname)

    evals, evecs = get_hessian_eigs(loss=criterion,
                         model=model, use_cuda=use_cuda, n_eigs=200,
                         loader=trainloader, evals=True)
    
    print("positive evals = ", evals)
    ## clean these guys up ##
    keep = np.where(evals.cpu() != 1)
    evals = evals[keep].squeeze()
    evecs = evecs[:, keep].squeeze()
    
    fname = "top_evecs.pt"
    torch.save(evecs, fpath + fname)
    fname = "top_evals.pt"
    torch.save(evals, fpath + fname)

if __name__ == '__main__':
    main()
