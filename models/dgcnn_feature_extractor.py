import torch.nn as nn
import torch.utils.data
import torch.nn.functional as F
from utils.dgcnn_util import get_graph_feature


class DGCNN_Feature_Extractor(nn.Module):
    def __init__(self, n_knn):
        super(DGCNN_Feature_Extractor, self).__init__()
        self.n_knn = n_knn
        
        self.bn1 = nn.BatchNorm2d(64)
        self.bn2 = nn.BatchNorm2d(64)
        self.bn3 = nn.BatchNorm2d(128)
        self.bn4 = nn.BatchNorm2d(256)
        self.bn5 = nn.BatchNorm1d(1024)

        self.conv1 = nn.Sequential(nn.Conv2d(8, 64, kernel_size=1, bias=False),
                                   self.bn1,
                                   nn.LeakyReLU(negative_slope=0.2))
        self.conv2 = nn.Sequential(nn.Conv2d(64*2, 64, kernel_size=1, bias=False),
                                   self.bn2,
                                   nn.LeakyReLU(negative_slope=0.2))
        self.conv3 = nn.Sequential(nn.Conv2d(64*2, 128, kernel_size=1, bias=False),
                                   self.bn3,
                                   nn.LeakyReLU(negative_slope=0.2))
        self.conv4 = nn.Sequential(nn.Conv2d(128*2, 256, kernel_size=1, bias=False),
                                   self.bn4,
                                   nn.LeakyReLU(negative_slope=0.2))
        self.conv5 = nn.Sequential(nn.Conv1d(512, 1024, kernel_size=1, bias=False),
                                   self.bn5,
                                   nn.LeakyReLU(negative_slope=0.2))
        
        # TODO: more layers???
        
        # self.linear1 = nn.Linear(1024*2, 512, bias=False)
        # self.bn6 = nn.BatchNorm1d(512)
        # self.dp1 = nn.Dropout(p=0.5)
        # self.linear2 = nn.Linear(512, 256)
        # self.bn7 = nn.BatchNorm1d(256)
        # self.dp2 = nn.Dropout(p=0.5)
        # self.linear3 = nn.Linear(256, num_class)

    def forward(self, x):
        batch_size = x.size(0)
        x = get_graph_feature(x, k=self.n_knn)
        x = self.conv1(x)
        x1 = x.max(dim=-1, keepdim=False)[0]

        x = get_graph_feature(x1, k=self.n_knn)
        x = self.conv2(x)
        x2 = x.max(dim=-1, keepdim=False)[0]

        x = get_graph_feature(x2, k=self.n_knn)
        x = self.conv3(x)
        x3 = x.max(dim=-1, keepdim=False)[0]

        x = get_graph_feature(x3, k=self.n_knn)
        x = self.conv4(x)
        x4 = x.max(dim=-1, keepdim=False)[0]

        x = torch.cat((x1, x2, x3, x4), dim=1)

        x = self.conv5(x)
        x1 = F.adaptive_max_pool1d(x, 1).view(batch_size, -1) # paper says max pool

        # no linears, because that throws away spatial info

        # x2 = F.adaptive_avg_pool1d(x, 1).view(batch_size, -1)
        # x = torch.cat((x1, x2), 1)

        # x = F.leaky_relu(self.bn6(self.linear1(x)), negative_slope=0.2)
        # x = self.dp1(x)
        # x = F.leaky_relu(self.bn7(self.linear2(x)), negative_slope=0.2)
        # x = self.dp2(x)
        # x = self.linear3(x)
        
        # trans_feat = None
        # return x, trans_feat

        x1 = F.normalize(x1, dim=1) # hyperspherical manifold
        assert torch.isclose(torch.sum(torch.pow(x1[0], 2)), 1)
        assert x1.shape == (batch_size, 1024)
        return x1