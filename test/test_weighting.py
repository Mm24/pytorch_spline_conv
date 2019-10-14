from itertools import product

import pytest
import torch
from torch.autograd import gradcheck
from torch_spline_conv.weighting import SplineWeighting
from torch_spline_conv.basis import SplineBasis

from .utils import dtypes, devices, tensor

tests = [{
    'x': [[1, 2], [3, 4]],
    'weight': [[[1], [2]], [[3], [4]], [[5], [6]], [[7], [8]]],
    'basis': [[0.5, 0, 0.5, 0], [0, 0, 0.5, 0.5]],
    'weight_index': [[0, 1, 2, 3], [0, 1, 2, 3]],
    'expected': [
        [0.5 * ((1 * (1 + 5)) + (2 * (2 + 6)))],
        [0.5 * ((3 * (5 + 7)) + (4 * (6 + 8)))],
    ]
}]


@pytest.mark.parametrize('test,dtype,device', product(tests, dtypes, devices))
def test_spline_weighting_forward(test, dtype, device):
    x = tensor(test['x'], dtype, device)
    weight = tensor(test['weight'], dtype, device)
    basis = tensor(test['basis'], dtype, device)
    weight_index = tensor(test['weight_index'], torch.long, device)

    out = SplineWeighting.apply(x, weight, basis, weight_index)
    assert out.tolist() == test['expected']


@pytest.mark.parametrize('device', devices)
def test_spline_weighting_backward(device):
    pseudo = torch.rand((4, 2), dtype=torch.double, device=device)
    kernel_size = tensor([5, 5], torch.long, device)
    is_open_spline = tensor([1, 1], torch.uint8, device)
    degree = 1

    op = SplineBasis.apply
    basis, weight_index = op(pseudo, kernel_size, is_open_spline, degree)
    basis.requires_grad_()

    x = torch.rand((4, 2), dtype=torch.double, device=device)
    x.requires_grad_()
    weight = torch.rand((25, 2, 4), dtype=torch.double, device=device)
    weight.requires_grad_()

    data = (x, weight, basis, weight_index)
    assert gradcheck(SplineWeighting.apply, data, eps=1e-6, atol=1e-4) is True
