from __future__ import print_function
import numpy as np
# import tensorflow as tf
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.nn.init as init

import time
import random
import math
import sys

sys.path.insert(0, "./models")
from networks import initialize_weights

class BasicBlock(nn.Module):
	expansion = 1

	def __init__(self, in_planes, planes, stride=1):
		super(BasicBlock, self).__init__()
		self.conv1 = nn.Conv2d(in_planes, planes, kernel_size=3, stride=stride, padding=1, bias=False)
		self.bn1 = nn.BatchNorm2d(planes)
		self.conv2 = nn.Conv2d(planes, planes, kernel_size=3, stride=1, padding=1, bias=False)
		self.bn2 = nn.BatchNorm2d(planes)
		self.relu = nn.LeakyReLU(negative_slope=0.2, inplace=True)

		self.shortcut = nn.Sequential()
		if stride != 1 or in_planes != self.expansion*planes:
			self.shortcut = nn.Sequential(
				nn.Conv2d(in_planes, self.expansion*planes, kernel_size=1, stride=stride, bias=False),
				nn.BatchNorm2d(self.expansion*planes)
			)

	def forward(self, x):
		out = self.relu(self.bn1(self.conv1(x)))
		out = self.bn2(self.conv2(out))
		out += self.shortcut(x)
		out = self.relu(out)
		return out


class Bottleneck(nn.Module):
	expansion = 4

	def __init__(self, in_planes, planes, stride=1):
		super(Bottleneck, self).__init__()
		self.conv1 = nn.Conv2d(in_planes, planes, kernel_size=1, bias=False)
		self.bn1 = nn.BatchNorm2d(planes)
		self.conv2 = nn.Conv2d(planes, planes, kernel_size=3, stride=stride, padding=1, bias=False)
		self.bn2 = nn.BatchNorm2d(planes)
		self.conv3 = nn.Conv2d(planes, self.expansion*planes, kernel_size=1, bias=False)
		self.bn3 = nn.BatchNorm2d(self.expansion*planes)
		self.relu = nn.LeakyReLU(negative_slope=0.2, inplace=True)

		self.shortcut = nn.Sequential()
		if stride != 1 or in_planes != self.expansion*planes:
			self.shortcut = nn.Sequential(
				nn.Conv2d(in_planes, self.expansion*planes, kernel_size=1, stride=stride, bias=False),
				nn.BatchNorm2d(self.expansion*planes)
			)

	def forward(self, x):
		out = self.relu(self.bn1(self.conv1(x)))
		out = self.relu(self.bn2(self.conv2(out)))
		out = self.bn3(self.conv3(out))
		out += self.shortcut(x)
		out = self.relu(out)
		return out


class PM25ResNet(nn.Module):
	def __init__(self, num_block, num_channel, num_input):
		super(PM25ResNet, self).__init__()
		if num_block < 50:
			block = BasicBlock
		else:
			block = Bottleneck
		self.in_planes = num_channel

		self.conv1 = nn.Conv2d(num_input, self.in_planes, kernel_size=3, stride=1, padding=1, bias=False)
		self.bn1 = nn.BatchNorm2d(self.in_planes)
		self.layer1 = self._make_layer(block, self.in_planes, num_block, stride=1)

		self.conv2 = nn.Conv2d(self.in_planes, self.in_planes, kernel_size=3, stride=1, padding=1, bias=False)
		self.bn2 = nn.BatchNorm2d(self.in_planes)
		self.conv3 = nn.Conv2d(self.in_planes, 1, kernel_size=3, stride=1, padding=1, bias=False)

		self.conv_skip = nn.Conv2d(self.in_planes, self.in_planes, kernel_size=3, stride=1, padding=1, bias=False)
		self.bn_skip = nn.BatchNorm2d(self.in_planes)

		self.relu = nn.LeakyReLU(negative_slope=0.2, inplace=True)

		initialize_weights([self.conv1, self.bn1, self.layer1, self.conv2, self.bn2, self.conv3, self.conv_skip, self.bn_skip], 0.1)

	def _make_layer(self, block, planes, num_blocks, stride):
		strides = [stride] + [1]*(num_blocks-1)
		layers = []
		for stride in strides:
			layers.append(block(self.in_planes, planes, stride))
			self.in_planes = planes * block.expansion
		return nn.Sequential(*layers)

	def forward(self, x):
		out = self.relu(self.bn1(self.conv1(x)))
		#skip = self.relu(self.bn_skip(self.conv_skip(out)))
		out = self.layer1(out)
		#out = self.relu(self.bn2(self.conv2(out))) + skip		
		out = self.relu(self.bn2(self.conv2(out)))
		out = self.conv3(out)

		return out




