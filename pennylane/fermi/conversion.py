# Copyright 2018-2023 Xanadu Quantum Technologies Inc.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Functions to convert a fermionic operator to the qubit basis."""

from functools import singledispatch
from typing import Union

import numpy as np

import pennylane as qml
from pennylane.operation import Operator
from pennylane.pauli import PauliSentence, PauliWord

from .fermionic import FermiSentence, FermiWord


def jordan_wigner(
    fermi_operator: Union[FermiWord, FermiSentence],
    ps: bool = False,
    wire_map: dict = None,
    tol: float = None,
) -> Union[Operator, PauliSentence]:
    r"""Convert a fermionic operator to a qubit operator using the Jordan-Wigner mapping.

    The fermionic creation and annihilation operators are mapped to the Pauli operators as

    .. math::

        a^{\dagger}_0 =  \left (\frac{X_0 - iY_0}{2}  \right ), \:\: \text{...,} \:\:
        a^{\dagger}_n = Z_0 \otimes Z_1 \otimes ... \otimes Z_{n-1} \otimes \left (\frac{X_n - iY_n}{2} \right ),

    and

    .. math::

        a_0 =  \left (\frac{X_0 + iY_0}{2}  \right ), \:\: \text{...,} \:\:
        a_n = Z_0 \otimes Z_1 \otimes ... \otimes Z_{n-1} \otimes \left (\frac{X_n + iY_n}{2}  \right ),

    where :math:`X`, :math:`Y`, and :math:`Z` are the Pauli operators.

    Args:
        fermi_operator(FermiWord, FermiSentence): the fermionic operator
        ps (bool): whether to return the result as a PauliSentence instead of an
            Operator. Defaults to False.
        wire_map (dict): a dictionary defining how to map the orbitals of
            the Fermi operator to qubit wires. If None, the integers used to
            order the orbitals will be used as wire labels. Defaults to None.
        tol (float): tolerance for discarding the imaginary part of the coefficients

    Returns:
        Union[PauliSentence, Operator]: a linear combination of qubit operators

    **Example**

    >>> w = qml.fermi.from_string('0+ 1-')
    >>> jordan_wigner(w)
    (
        -0.25j * (Y(0) @ X(1))
      + (0.25+0j) * (Y(0) @ Y(1))
      + (0.25+0j) * (X(0) @ X(1))
      + 0.25j * (X(0) @ Y(1))
    )

    >>> jordan_wigner(w, ps=True)
    -0.25j * Y(0) @ X(1)
    + (0.25+0j) * Y(0) @ Y(1)
    + (0.25+0j) * X(0) @ X(1)
    + 0.25j * X(0) @ Y(1)

    >>> jordan_wigner(w, ps=True, wire_map={0: 2, 1: 3})
    -0.25j * Y(2) @ X(3)
    + (0.25+0j) * Y(2) @ Y(3)
    + (0.25+0j) * X(2) @ X(3)
    + 0.25j * X(2) @ Y(3)
    """
    return _jordan_wigner_dispatch(fermi_operator, ps, wire_map, tol)


@singledispatch
def _jordan_wigner_dispatch(fermi_operator, ps, wire_map, tol):
    """Dispatches to appropriate function if fermi_operator is a FermiWord or FermiSentence."""
    raise ValueError(f"fermi_operator must be a FermiWord or FermiSentence, got: {fermi_operator}")


@_jordan_wigner_dispatch.register
def _(fermi_operator: FermiWord, ps=False, wire_map=None, tol=None):
    wires = list(fermi_operator.wires) or [0]
    identity_wire = wires[0]

    if len(fermi_operator) == 0:
        qubit_operator = PauliSentence({PauliWord({}): 1.0})
    else:
        coeffs = {"+": -0.5j, "-": 0.5j}
        qubit_operator = PauliSentence({PauliWord({}): 1.0})

        for (_, wire), sign in fermi_operator.items():
            z_string = {i: "Z" for i in range(wire)}
            x_term = PauliWord({**z_string, wire: "X"})
            y_term = PauliWord({**z_string, wire: "Y"})

            qubit_operator @= PauliSentence({x_term: 0.5, y_term: coeffs[sign]})

    if tol is not None:
        qubit_operator = PauliSentence({
            pw: qml.math.real(coeff) if abs(qml.math.imag(coeff)) <= tol else coeff
            for pw, coeff in qubit_operator.items()
        })

    if not ps:
        qubit_operator = qubit_operator.operation(wire_order=[identity_wire])

    if wire_map:
        return qubit_operator.map_wires(wire_map)

    return qubit_operator


@_jordan_wigner_dispatch.register
def _(fermi_operator: FermiSentence, ps=False, wire_map=None, tol=None):
    wires = list(fermi_operator.wires) or [0]
    identity_wire = wires[0]

    qubit_operator = PauliSentence()

    for fw, coeff in fermi_operator.items():
        fermi_word_as_ps = jordan_wigner(fw, ps=True)

        for pw, pw_coeff in fermi_word_as_ps.items():
            total_coeff = qubit_operator.get(pw, 0) + pw_coeff * coeff
            if tol is not None and abs(qml.math.imag(total_coeff)) <= tol:
                total_coeff = qml.math.real(total_coeff)
            qubit_operator[pw] = total_coeff

    qubit_operator.simplify(tol=1e-16)

    if not ps:
        qubit_operator = qubit_operator.operation(wire_order=[identity_wire])

    if wire_map:
        return qubit_operator.map_wires(wire_map)

    return qubit_operator


def parity_transform(
    fermi_operator: Union[FermiWord, FermiSentence],
    n: int,
    ps: bool = False,
    wire_map: dict = None,
    tol: float = None,
) -> Union[Operator, PauliSentence]:
    r"""Convert a fermionic operator to a qubit operator using the parity mapping.

    .. note::

        Hamiltonians created with this mapping should be used with operators and states that are
        compatible with the parity basis.

    In parity mapping, qubit :math:`j` stores the parity of all :math:`j-1` qubits before it.
    In comparison, :func:`~.jordan_wigner` simply uses qubit :math:`j` to store the occupation number.
    In parity mapping, the fermionic creation and annihilation operators are mapped to the Pauli operators as

    .. math::
        \begin{align*}
           a^{\dagger}_0 &= \left (\frac{X_0 - iY_0}{2}  \right )\otimes X_1 \otimes X_2 \otimes ... X_n, \\\\
           a^{\dagger}_n &= \left (\frac{Z_{n-1} \otimes X_n - iY_n}{2} \right ) \otimes X_{n+1} \otimes X_{n+2} \otimes ... \otimes X_n
        \end{align*}

    and

    .. math::
        \begin{align*}
           a_0 &= \left (\frac{X_0 + iY_0}{2}  \right )\otimes X_1 \otimes X_2 \otimes ... X_n,\\\\
           a_n &= \left (\frac{Z_{n-1} \otimes X_n + iY_n}{2} \right ) \otimes X_{n+1} \otimes X_{n+2} \otimes ... \otimes X_n
        \end{align*}

    where :math:`X`, :math:`Y`, and :math:`Z` are the Pauli operators and :math:`n` is the number of qubits, i.e., spin orbitals.

    Args:
        fermi_operator(FermiWord, FermiSentence): the fermionic operator
        n (int): number of qubits, i.e., spin orbitals in the system
        ps (bool): whether to return the result as a :class:`~.PauliSentence` instead of an
            :class:`~.Operator`. Defaults to ``False``.
        wire_map (dict): a dictionary defining how to map the orbitals of
            the Fermi operator to qubit wires. If ``None``, the integers used to
            order the orbitals will be used as wire labels. Defaults to ``None``.
        tol (float): tolerance for discarding the imaginary part of the coefficients

    Returns:
        Union[PauliSentence, Operator]: a linear combination of qubit operators

    **Example**

    >>> w = qml.fermi.from_string('0+ 1-')
    >>> parity_transform(w, n=6)
    (
        -0.25j * Y(0)
      + (-0.25+0j) * (X(0) @ Z(1))
      + (0.25+0j) * X(0)
      + 0.25j * (Y(0) @ Z(1))
    )

    >>> parity_transform(w, n=6, ps=True)
    -0.25j * Y(0)
    + (-0.25+0j) * X(0) @ Z(1)
    + (0.25+0j) * X(0)
    + 0.25j * Y(0) @ Z(1)

    >>> parity_transform(w, n=6, ps=True, wire_map={0: 2, 1: 3})
    -0.25j * Y(2)
    + (-0.25+0j) * X(2) @ Z(3)
    + (0.25+0j) * X(2)
    + 0.25j * Y(2) @ Z(3)
    """

    return _parity_transform_dispatch(fermi_operator, n, ps, wire_map, tol)


@singledispatch
def _parity_transform_dispatch(fermi_operator, n, ps, wire_map, tol):
    """Dispatches to appropriate function if fermi_operator is a FermiWord or FermiSentence."""
    raise ValueError(f"fermi_operator must be a FermiWord or FermiSentence, got: {fermi_operator}")


@_parity_transform_dispatch.register
def _(fermi_operator: FermiWord, n, ps=False, wire_map=None, tol=None):
    wires = list(fermi_operator.wires) or [0]
    identity_wire = wires[0]

    coeffs = {"+": -0.5j, "-": 0.5j}
    qubit_operator = PauliSentence({PauliWord({}): 1.0})

    for (_, wire), sign in fermi_operator.items():
        if wire >= n:
            raise ValueError(
                f"Can't create or annihilate a particle on qubit number {wire} for a system with only {n} qubits"
            )

        x_string = {i: "X" for i in range(wire + 1, n)}
        if wire == 0:
            pw1 = PauliWord({**{wire: "X"}, **x_string})
        else:
            pw1 = PauliWord({**{wire - 1: "Z", wire: "X"}, **x_string})
        pw2 = PauliWord({**{wire: "Y"}, **x_string})

        qubit_operator @= PauliSentence({pw1: 0.5, pw2: coeffs[sign]})

    if tol is not None:
        qubit_operator = PauliSentence({
            pw: qml.math.real(coeff) if abs(qml.math.imag(coeff)) <= tol else coeff
            for pw, coeff in qubit_operator.items()
        })

    if not ps:
        qubit_operator = qubit_operator.operation(wire_order=[identity_wire])

    if wire_map:
        return qubit_operator.map_wires(wire_map)

    return qubit_operator


@_parity_transform_dispatch.register
def _(fermi_operator: FermiSentence, n, ps=False, wire_map=None, tol=None):
    wires = list(fermi_operator.wires) or [0]
    identity_wire = wires[0]

    qubit_operator = PauliSentence()

    for fw, coeff in fermi_operator.items():
        fermi_word_as_ps = parity_transform(fw, n, ps=True)

        for pw, pw_coeff in fermi_word_as_ps.items():
            total_coeff = qubit_operator.get(pw, 0) + pw_coeff * coeff
            if tol is not None and abs(qml.math.imag(total_coeff)) <= tol:
                total_coeff = qml.math.real(total_coeff)
            qubit_operator[pw] = total_coeff

    qubit_operator.simplify(tol=1e-16)

    if not ps:
        qubit_operator = qubit_operator.operation(wire_order=[identity_wire])

    if wire_map:
        return qubit_operator.map_wires(wire_map)

    return qubit_operator


def bravyi_kitaev(
    fermi_operator: Union[FermiWord, FermiSentence],
    n: int,
    ps: bool = False,
    wire_map: dict = None,
    tol: float = None,
) -> Union[Operator, PauliSentence]:
    r"""Convert a fermionic operator to a qubit operator using the Bravyi-Kitaev mapping.

    .. note::

        Hamiltonians created with this mapping should be used with operators and states that are
        compatible with the Bravyi-Kitaev basis.

    In the Bravyi-Kitaev mapping, both occupation number and parity of the orbitals are stored non-locally.
    In comparison, :func:`~.jordan_wigner` stores the occupation number locally while storing the parity
    non-locally and vice-versa for :func:`~.parity_transform`. In the Bravyi-Kitaev mapping, the
    fermionic creation and annihilation operators for even-labelled orbitals are mapped to the Pauli operators as

    .. math::

        \begin{align*}
           a^{\dagger}_0 &= \frac{1}{2} \left ( X_0  -iY_{0} \right ), \\\\
           a^{\dagger}_n &= \frac{1}{2} \left ( X_{U(n)} \otimes X_n \otimes Z_{P(n)} -iX_{U(n)} \otimes Y_{n} \otimes Z_{P(n)}\right ), \\\\
        \end{align*}

    and

    .. math::

        \begin{align*}
           a_n &= \frac{1}{2} \left ( X_{U(n)} \otimes X_n \otimes Z_{P(n)} +iX_{U(n)} \otimes Y_{n} \otimes Z_{P(n)}\right ). \\\\
        \end{align*}

    Similarly, the fermionic creation and annihilation operators for odd-labelled orbitals are mapped to the Pauli operators as

    .. math::
        \begin{align*}
           a^{\dagger}_n &= \frac{1}{2} \left ( X_{U(n)} \otimes X_n \otimes Z_{P(n)} -iX_{U(n)} \otimes Y_{n} \otimes Z_{R(n)}\right ), \\\\
        \end{align*}

    and

    .. math::
        \begin{align*}
           a_n &= \frac{1}{2} \left ( X_{U(n)} \otimes X_n \otimes Z_{P(n)} +iX_{U(n)} \otimes Y_{n} \otimes Z_{R(n)}\right ), \\\\
        \end{align*}

    where :math:`X`, :math:`Y`, and :math:`Z` are the Pauli operators, and :math:`U(n)`, :math:`P(n)` and :math:`R(n)`
    represent the update, parity and remainder sets, respectively [`arXiv:1812.02233 <https://arxiv.org/abs/1812.02233>`_].

    Args:
        fermi_operator(FermiWord, FermiSentence): the fermionic operator
        n (int): number of qubits, i.e., spin orbitals in the system
        ps (bool): whether to return the result as a PauliSentence instead of an
            Operator. Defaults to False.
        wire_map (dict): a dictionary defining how to map the orbitals of
            the Fermi operator to qubit wires. If None, the integers used to
            order the orbitals will be used as wire labels. Defaults to None.
        tol (float): tolerance for discarding the imaginary part of the coefficients

    Returns:
        Union[PauliSentence, Operator]: a linear combination of qubit operators

    **Example**

    >>> w = qml.fermi.from_string('0+ 1-')
    >>> bravyi_kitaev(w, n=6)
    (
        -0.25j * Y(0)
      + (-0.25+0j) * (X(0) @ Z(1))
      + (0.25+0j) * X(0)
      + 0.25j * (Y(0) @ Z(1))
    )

    >>> bravyi_kitaev(w, n=6, ps=True)
    -0.25j * Y(0)
    + (-0.25+0j) * X(0) @ Z(1)
    + (0.25+0j) * X(0)
    + 0.25j * Y(0) @ Z(1)

    >>> bravyi_kitaev(w, n=6, ps=True, wire_map={0: 2, 1: 3})
    -0.25j * Y(2)
    + (-0.25+0j) * X(2) @ Z(3)
    + (0.25+0j) * X(2)
    + 0.25j * Y(2) @ Z(3)

    """
    return _bravyi_kitaev_dispatch(fermi_operator, n, ps, wire_map, tol)


def _update_set(j, bin_range, n):
    """
    Computes the update set of the j-th orbital in n qubits.

    Args:
        j (int): the orbital index
        bin_range (int): smallest power of 2 equal to or greater than n
        n (int): number of qubits

    Returns:
        list: List containing the update set
    """
    indices = []
    midpoint = bin_range // 2
    if bin_range % 2 != 0:
        return indices

    if j < midpoint:
        indices.append(bin_range - 1)
        indices.extend(_update_set(j, midpoint, n))
    else:
        indices.extend(u + midpoint for u in _update_set(j - midpoint, midpoint, n))

    return [u for u in indices if u < n]


def _parity_set(j, bin_range):
    """
    Computes the parity set of the j-th orbital.

    Args:
        j (int): the orbital index
        bin_range (int): smallest power of 2 equal to or greater than n

    Returns:
        list: List of qubits which determine the parity of qubit j
    """
    indices = []
    midpoint = bin_range // 2
    if bin_range % 2 != 0:
        return indices

    if j < midpoint:
        indices.extend(_parity_set(j, midpoint))
    else:
        indices.extend(_parity_set(j - midpoint, midpoint))
        indices.append(midpoint - 1)

    return indices


def _flip_set(j, bin_range):
    """
    Computes the flip set of the j-th orbital.

    Args:
        j (int): the orbital index
        bin_range (int): smallest power of 2 equal to or greater than n

    Returns:
        list: List containing information if the phase of orbital j is same as qubit j.
    """
    indices = []
    midpoint = bin_range // 2
    if bin_range % 2 != 0:
        return indices

    if j < midpoint:
        indices.extend(_flip_set(j, midpoint))
    elif midpoint <= j < bin_range - 1:
        indices.extend(u + midpoint for u in _flip_set(j - midpoint, midpoint))
    else:
        indices.extend(u + midpoint for u in _flip_set(j - midpoint, midpoint))
        indices.append(midpoint - 1)

    return indices


@singledispatch
def _bravyi_kitaev_dispatch(fermi_operator, n, ps, wire_map, tol):
    """Dispatches to appropriate function if fermi_operator is a FermiWord or FermiSentence."""
    raise ValueError(f"fermi_operator must be a FermiWord or FermiSentence, got: {fermi_operator}")


@_bravyi_kitaev_dispatch.register
def _(fermi_operator: FermiWord, n, ps=False, wire_map=None, tol=None):
    wires = list(fermi_operator.wires) or [0]
    identity_wire = wires[0]

    coeffs = {"+": -0.5j, "-": 0.5j}
    qubit_operator = PauliSentence({PauliWord({}): 1.0})

    bin_range = 2 ** int(np.ceil(np.log2(n)))

    for (_, wire), sign in fermi_operator.items():
        if wire >= n:
            raise ValueError(
                f"Can't create or annihilate a particle on qubit index {wire} for a system with only {n} qubits."
            )

        u_set = _update_set(wire, bin_range, n)
        update_string = {u: "X" for u in u_set}

        p_set = _parity_set(wire, bin_range)
        parity_string = {p: "Z" for p in p_set}

        if wire % 2 == 0:
            x_term = PauliWord({**parity_string, wire: "X", **update_string})
            y_term = PauliWord({**parity_string, wire: "Y", **update_string})
        else:
            f_set = _flip_set(wire, bin_range)
            r_set = [p for p in p_set if p not in f_set]
            remainder_string = {r: "Z" for r in r_set}

            x_term = PauliWord({**parity_string, wire: "X", **update_string})
            y_term = PauliWord({**remainder_string, wire: "Y", **update_string})

        qubit_operator @= PauliSentence({x_term: 0.5, y_term: coeffs[sign]})

    if tol is not None:
        qubit_operator = PauliSentence({
            pw: qml.math.real(coeff) if abs(qml.math.imag(coeff)) <= tol else coeff
            for pw, coeff in qubit_operator.items()
        })

    if not ps:
        qubit_operator = qubit_operator.operation(wire_order=[identity_wire])

    if wire_map:
        return qubit_operator.map_wires(wire_map)

    return qubit_operator


@_bravyi_kitaev_dispatch.register
def _(fermi_operator: FermiSentence, n, ps=False, wire_map=None, tol=None):
    wires = list(fermi_operator.wires) or [0]
    identity_wire = wires[0]

    qubit_operator = PauliSentence()

    for fw, coeff in fermi_operator.items():
        fermi_word_as_ps = bravyi_kitaev(fw, n, ps=True)

        for pw, pw_coeff in fermi_word_as_ps.items():
            total_coeff = qubit_operator.get(pw, 0) + pw_coeff * coeff
            if tol is not None and abs(qml.math.imag(total_coeff)) <= tol:
                total_coeff = qml.math.real(total_coeff)
            qubit_operator[pw] = total_coeff

    qubit_operator.simplify(tol=1e-16)

    if not ps:
        qubit_operator = qubit_operator.operation(wire_order=[identity_wire])

    if wire_map:
        return qubit_operator.map_wires(wire_map)

    return qubit_operator
