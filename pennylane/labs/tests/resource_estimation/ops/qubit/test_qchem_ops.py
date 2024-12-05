# Copyright 2024 Xanadu Quantum Technologies Inc.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for qchem ops resource operators."""

import pennylane.labs.resource_estimation as re

# pylint: disable=use-implicit-booleaness-not-comparison,no-self-use


class TestSingleExcitationMinus:
    """Tests for the ResourceSingleExcitationMinus class."""

    def test_resources(self):
        """Test that the resources are correct."""
        expected = {
            re.ResourceX.resource_rep(): 4,
            re.ResourceControlledPhaseShift.resource_rep(): 2,
            re.ResourceCNOT.resource_rep(): 2,
            re.ResourceCRY.resource_rep(): 1,
        }
        assert re.ResourceSingleExcitationMinus.resources() == expected

    def test_resource_params(self):
        """Test that the resource params are correct."""
        op = re.ResourceSingleExcitationMinus(0.5, wires=[0, 1])
        assert op.resource_params() == {}

    def test_resource_rep(self):
        """Test that the compressed representation is correct."""
        expected = re.CompressedResourceOp(re.ResourceSingleExcitationMinus, {})
        assert re.ResourceSingleExcitationMinus.resource_rep() == expected

    def test_resources_from_rep(self):
        """Test that the resources can be obtained from the compressed representation."""
        op = re.ResourceSingleExcitationMinus(0.5, wires=[0, 1])
        expected = {
            re.ResourceX.resource_rep(): 4,
            re.ResourceControlledPhaseShift.resource_rep(): 2,
            re.ResourceCNOT.resource_rep(): 2,
            re.ResourceCRY.resource_rep(): 1,
        }
        op_compressed_rep = op.resource_rep_from_op()
        op_resource_type = op_compressed_rep.op_type
        op_resource_params = op_compressed_rep.params
        assert op_resource_type.resources(**op_resource_params) == expected


class TestSingleExcitationPlus:
    """Tests for the ResourceSingleExcitationPlus class."""

    def test_resources(self):
        """Test that the resources are correct."""
        expected = {
            re.ResourceX.resource_rep(): 4,
            re.ResourceControlledPhaseShift.resource_rep(): 2,
            re.ResourceCNOT.resource_rep(): 2,
            re.ResourceCRY.resource_rep(): 1,
        }
        assert re.ResourceSingleExcitationPlus.resources() == expected

    def test_resource_params(self):
        """Test that the resource params are correct."""
        op = re.ResourceSingleExcitationPlus(0.5, wires=[0, 1])
        assert op.resource_params() == {}

    def test_resource_rep(self):
        """Test that the compressed representation is correct."""
        expected = re.CompressedResourceOp(re.ResourceSingleExcitationPlus, {})
        assert re.ResourceSingleExcitationPlus.resource_rep() == expected

    def test_resources_from_rep(self):
        """Test that the resources can be obtained from the compressed representation."""
        op = re.ResourceSingleExcitationPlus(0.5, wires=[0, 1])
        expected = {
            re.ResourceX.resource_rep(): 4,
            re.ResourceControlledPhaseShift.resource_rep(): 2,
            re.ResourceCNOT.resource_rep(): 2,
            re.ResourceCRY.resource_rep(): 1,
        }
        op_compressed_rep = op.resource_rep_from_op()
        op_resource_type = op_compressed_rep.op_type
        op_resource_params = op_compressed_rep.params
        assert op_resource_type.resources(**op_resource_params) == expected


class TestDoubleExcitation:
    """Tests for the ResourceDoubleExcitation class."""

    def test_resources(self):
        """Test that the resources are correct."""
        expected = {
            re.ResourceHadamard.resource_rep(): 6,
            re.ResourceRY.resource_rep(): 8,
            re.ResourceCNOT.resource_rep(): 14,
        }
        assert re.ResourceDoubleExcitation.resources() == expected

    def test_resource_params(self):
        """Test that the resource params are correct."""
        op = re.ResourceDoubleExcitation(0.5, wires=[0, 1, 2, 3])
        assert op.resource_params() == {}

    def test_resource_rep(self):
        """Test that the compressed representation is correct."""
        expected = re.CompressedResourceOp(re.ResourceDoubleExcitation, {})
        assert re.ResourceDoubleExcitation.resource_rep() == expected

    def test_resources_from_rep(self):
        """Test that the resources can be obtained from the compressed representation."""
        op = re.ResourceDoubleExcitation(0.5, wires=[0, 1, 2, 3])
        expected = {
            re.ResourceHadamard.resource_rep(): 6,
            re.ResourceRY.resource_rep(): 8,
            re.ResourceCNOT.resource_rep(): 14,
        }
        op_compressed_rep = op.resource_rep_from_op()
        op_resource_type = op_compressed_rep.op_type
        op_resource_params = op_compressed_rep.params
        assert op_resource_type.resources(**op_resource_params) == expected


class TestFermionicSWAP:
    """Tests for the ResourceFermionicSWAP class."""

    def test_resources(self):
        """Test that the resources are correct."""
        expected = {
            re.ResourceHadamard.resource_rep(): 4,
            re.ResourceMultiRZ.resource_rep(num_wires=2): 2,
            re.ResourceRX.resource_rep(): 4,
            re.ResourceRZ.resource_rep(): 2,
            re.ResourceGlobalPhase.resource_rep(): 1,
        }
        assert re.ResourceFermionicSWAP.resources() == expected

    def test_resource_params(self):
        """Test that the resource params are correct."""
        op = re.ResourceFermionicSWAP(0.5, wires=[0, 1])
        assert op.resource_params() == {}

    def test_resource_rep(self):
        """Test that the compressed representation is correct."""
        expected = re.CompressedResourceOp(re.ResourceFermionicSWAP, {})
        assert re.ResourceFermionicSWAP.resource_rep() == expected

    def test_resources_from_rep(self):
        """Test that the resources can be obtained from the compressed representation."""
        op = re.ResourceFermionicSWAP(0.5, wires=[0, 1])
        expected = {
            re.ResourceHadamard.resource_rep(): 4,
            re.ResourceMultiRZ.resource_rep(num_wires=2): 2,
            re.ResourceRX.resource_rep(): 4,
            re.ResourceRZ.resource_rep(): 2,
            re.ResourceGlobalPhase.resource_rep(): 1,
        }
        op_compressed_rep = op.resource_rep_from_op()
        op_resource_type = op_compressed_rep.op_type
        op_resource_params = op_compressed_rep.params
        assert op_resource_type.resources(**op_resource_params) == expected