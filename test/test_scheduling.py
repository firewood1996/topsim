# Copyright (C) 22/3/21 RW Bunney

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Test the scheduling algorithm as 'designed' by the user.
"""

import unittest

from topsim.user.scheduling import FifoAlgorithm


class TestFifoAlgorithm(unittest.TestCase):

    def setUp(self):
        self.algorithm = FifoAlgorithm()
        # TODO setup a workflow
        self.workflow = None

