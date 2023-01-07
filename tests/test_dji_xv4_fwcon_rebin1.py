# -*- coding: utf-8 -*-

""" Test for dji-firmware-tools, dji_xv4_fwcon script.

    This test verifies functions of the script by extracting some
    packages, re-packing them and checking if the resulting files
    are identical.
"""

# Copyright (C) 2023 Mefistotelis <mefistotelis@gmail.com>
# Copyright (C) 2023 Original Gangsters <https://dji-rev.slack.com/>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import filecmp
import glob
import itertools
import logging
import os
import re
import sys
import pathlib
import pytest
from unittest.mock import patch

# Import the functions to be tested
sys.path.insert(0, './')
from dji_xv4_fwcon import main as dji_xv4_fwcon_main


LOGGER = logging.getLogger(__name__)

@pytest.mark.parametrize("pkg_inp_fn", [fn for fn in itertools.chain.from_iterable([ glob.glob(e) for e in (
    './fw_packages/a3-flight_controller/*.bin',
    './fw_packages/ag405-agras_mg_1s_octocopter/*.bin',
    './fw_packages/ai900_agr-a3_based_multicopter_platform/*.bin',
    './fw_packages/am603-n3_based_multicopter_platform/*.bin',
    './fw_packages/d_rtk-mobile_station/*.bin',
    './fw_packages/ennn-esc/*.bin',
    './fw_packages/gl300abc-radio_control/*.bin',
    './fw_packages/gl300e-radio_control/*.bin',
    './fw_packages/hg211-osmo_pocket_2/*.bin',
    './fw_packages/hg300-osmo_mobile/*.bin',
    './fw_packages/hg301-osmo_mobile_2/*.bin',
    './fw_packages/hg910-ronin2_gimbal/*.bin',
    './fw_packages/lbtx-lightbridge_2_video_tx/*.bin',
    './fw_packages/m100-matrice_100_quadcopter/*.bin',
    './fw_packages/m600-matrice_600_hexacopter/*.bin',
    './fw_packages/m600pro-matrice_600_pro_hexacopter/*.bin',
    './fw_packages/n3-flight_controller/*.bin',
    './fw_packages/osmo-osmo_x3_gimbal/*.bin',
    './fw_packages/osmo_action-sport_cam/*.bin',
    './fw_packages/osmo_fc350z-osmo_zoom_z3_gimbal/*.bin',
    './fw_packages/osmo_fc550-osmo_x5_gimbal/*.bin',
    './fw_packages/osmo_fc550r-osmo_x5raw_gimbal/*.bin',
    './fw_packages/ot110-osmo_pocket_gimbal/*.bin',
    './fw_packages/p3c-phantom_3_std_quadcopter/*.bin',
    './fw_packages/p3s-phantom_3_adv_quadcopter/*.bin',
    './fw_packages/p3se-phantom_3_se_quadcopter/*.bin',
    './fw_packages/p3x-phantom_3_pro_quadcopter/*.bin',
    './fw_packages/p3xw-phantom_3_4k_quadcopter/*.bin',
    './fw_packages/swr60g-matrice_600_swr_60g/*.bin',
    './fw_packages/wind-a3_based_multicopter_platform/*.bin',
    './fw_packages/wm610-t600_inspire_1_x3_quadcopter/*.bin',
    './fw_packages/wm610_fc350z-t600_inspire_1_z3_quadcopter/*.bin',
    './fw_packages/wm610_fc550-t600_inspire_1_pro_x5_quadcopter/*.bin',
    './fw_packages/zt300-datalink_pro/*.bin',
  ) ]) if os.path.isfile(fn)] )
def test_dji_xv4_fwcon_rebin(pkg_inp_fn):
    """ Test extraction and re-creation of BIN package files.
    """
    # Most files we are able to recreate with full accuracy
    expect_file_identical = True

    # Special cases - ignoring differences for some specific files
    # Some files have zero-sized module at end, we do not support that properly
    if (pkg_inp_fn.endswith("OSMO_ACTION_FW_V01.10.00.40.bin")):
        LOGGER.warning("Expected non-identical binary due to zero-sized module at end: {:s}".format(pkg_inp_fn))
        expect_file_identical = False

    inp_path, inp_filename = os.path.split(pkg_inp_fn)
    inp_path = pathlib.Path(inp_path)
    inp_basename, pkg_fileext = os.path.splitext(inp_filename)
    if len(inp_path.parts) > 1:
        out_path = os.sep.join(["out"] + list(inp_path.parts[1:]))
    else:
        out_path = "out"
    modules_path1 = os.sep.join([out_path, "{:s}-split1".format(inp_basename)])
    if not os.path.exists(modules_path1):
        os.makedirs(modules_path1)
    xml_out_fn = os.sep.join([modules_path1, "{:s}.xml".format(inp_basename)])
    pkg_out_fn = os.sep.join([out_path, "{:s}.bin".format(inp_basename)])
    # Extract the package
    command = [os.path.join(".", "dji_xv4_fwcon.py"), "-vvv", "-x", "-p", pkg_inp_fn, "-m", xml_out_fn]
    LOGGER.info(' '.join(command))
    with patch.object(sys, 'argv', command):
        dji_xv4_fwcon_main()
    # Re-pack the package
    command = [os.path.join(".", "dji_xv4_fwcon.py"), "-vvv", "-a", "-m", xml_out_fn, "-p", pkg_out_fn]
    LOGGER.info(' '.join(command))
    with patch.object(sys, 'argv', command):
        dji_xv4_fwcon_main()
    if expect_file_identical:
        # Compare repackaged file and the original byte-to-byte
        match =  filecmp.cmp(pkg_inp_fn, pkg_out_fn, shallow=False)
        assert match, "Re-created file different: {:s}".format(pkg_inp_fn)
    else:
        # Check if repackaged file size roughly matches the original
        pkg_inp_fsize = os.path.getsize(pkg_inp_fn)
        pkg_out_fsize = os.path.getsize(pkg_out_fn)
        assert pkg_out_fsize >= int(pkg_inp_fsize * 0.95), "Re-created file too small: {:s}".format(pkg_inp_fn)
        assert pkg_out_fsize <= int(pkg_inp_fsize * 1.05), "Re-created file too large: {:s}".format(pkg_inp_fn)
    pass