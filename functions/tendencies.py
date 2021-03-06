
"""
    Tendencies definition module
    ============================

    This module provides functions to create the tendencies functions of the model, based on
    its parameters.

"""
import numpy as np
from numba import njit

from inner_products.analytic import AtmosphericInnerProducts, OceanicInnerProducts
from tensors.qgtensor import QgsTensor
from functions.sparse import sparse_mul3, sparse_mul2


def create_tendencies(params, return_inner_products=False, return_qgtensor=False):
    """Function to handle the inner products and tendencies tensors construction.
    Returns the tendencies function :math:`\\boldsymbol{f}` determining the model's ordinary differential
    equations:

    .. math:: \dot{\\boldsymbol{x}} = \\boldsymbol{f}(\\boldsymbol{x})

    which is for the model's integration.

    It returns also the linearized tendencies
    :math:`\\boldsymbol{\mathrm{J}} \equiv \\boldsymbol{\mathrm{D}f} = \\frac{\partial \\boldsymbol{f}}{\partial \\boldsymbol{x}}`
    (Jacobian matrix) which are used by the tangent linear model:

    .. math :: \dot{\\boldsymbol{\delta x}} = \\boldsymbol{\mathrm{J}}(\\boldsymbol{x}) \cdot \\boldsymbol{\delta x}

    Parameters
    ----------
    params: ~params.params.QgParams
        The parameters fully specifying the model configuration.
    return_inner_products: bool
        If True, return the inner products of the model. Default to False.
    return_qgtensor: bool
        If True, return the tendencies tensor of the model. Default to False.


    Returns
    -------
    f: callable
        The numba-jitted tendencies function.
    Df: callable
        The numba-jitted linearized tendencies function.
    inner_products: (AtmosphericInnerProducts, OceanicInnerProducts)
        If `return_inner_products` is True, the inner products of the system.
    qgtensor: QgsTensor
        If `return_qgtensor` is True, the tendencies tensor of the system.
    """

    if params.ablocks is not None:
        aip = AtmosphericInnerProducts(params)
    else:
        aip = None

    if params.goblocks is not None and params.gotemperature_params._name == "Oceanic Temperature":
        oip = OceanicInnerProducts(params)
    else:
        oip = None

    if aip is not None and oip is not None:
        aip.connect_to_ocean(oip)

    agotensor = QgsTensor(aip, oip)

    coo = agotensor.tensor.coords.T
    val = agotensor.tensor.data

    @njit
    def f(t, x):
        xx = np.concatenate((np.full((1,), 1.), x))
        xr = sparse_mul3(coo, val, xx, xx)

        return xr[1:]

    jcoo = agotensor.jacobian_tensor.coords.T
    jval = agotensor.jacobian_tensor.data

    @njit
    def Df(t, x):
        xx = np.concatenate((np.full((1,), 1.), x))
        mul_jac = sparse_mul2(jcoo, jval, xx)
        return mul_jac[1:, 1:]

    ret = list()
    ret.append(f)
    ret.append(Df)
    if return_inner_products:
        ret.append((aip, oip))
    if return_qgtensor:
        ret.append(agotensor)
    return ret


