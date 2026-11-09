import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.nn.init as init

width = 256

class mul_input_seq(nn.Sequential):
	def forward(self, *inputs):
		for module in self._modules.values():
			inputs = module(*inputs)
		return inputs

class SnoBN(nn.Module):
	def __init__(self, planes):
		super(SnoBN, self).__init__()
		self.bn = nn.BatchNorm2d(planes)
		self.fc1 = nn.Linear(4, width)
		self.fc_mul = nn.Linear(width, planes)
		self.fc_add = nn.Linear(width, planes)
		self.relu = nn.LeakyReLU(negative_slope=0.2, inplace=True)
	
	def forward(self, x, sno):
		x = self.bn(x)
		base = self.fc1(sno)
		base = self.relu(base)
		return x * self.fc_mul(base).unsqueeze(-1).unsqueeze(-1) + self.fc_add(base).unsqueeze(-1).unsqueeze(-1)

def initialize_weights(net_l, scale=1):
	if not isinstance(net_l, list):
		net_l = [net_l]
	for net in net_l:
		for m in net.modules():
			if isinstance(m, nn.Conv2d):
				init.kaiming_normal_(m.weight, a=0, mode='fan_in')
				m.weight.data *= scale  # for residual block
				if m.bias is not None:
					m.bias.data.zero_()
			elif isinstance(m, nn.Linear):
				init.kaiming_normal_(m.weight, a=0, mode='fan_in')
				m.weight.data *= scale
				if m.bias is not None:
					m.bias.data.zero_()
			elif isinstance(m, nn.BatchNorm2d):
				init.constant_(m.weight, 1)
				init.constant_(m.bias.data, 0.0)