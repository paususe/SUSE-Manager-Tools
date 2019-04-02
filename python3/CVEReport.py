#!/usr/bin/env python3
#
# CVEReport
#
# (c) 2019 SUSE Linux GmbH, Germany.
# GNU Public License. No warranty. No support
# For question/suggestions/bugs mail: michael.brookhuis@suse.com
#
# Version: 2019-02-12
#
# Created by: SUSE Michael Brookhuis
#
# This script will generate an comma-delimited file with system effected.
#
# Releases:
# 2019-02-12 M.Brookhuis - initial release.
#
#
#
#
"""
CVE report.
"""

import argparse
from argparse import RawTextHelpFormatter
import datetime
import smtools

smt = smtools.SMTools()


def create_file_cve(cve_data, fn):
    file = open(fn, "w")
    if not cve_data:
        file.write("NO CVE\n")
    else:
        file.write("System Name;CVE;Patch-Name;Patch available,channel containing patch;Packages included\n")
        for x in cve_data:
            file.write(x[0])
            file.write(";")
            file.write(x[1])
            file.write(";")
            file.write(x[2])
            file.write(";")
            file.write(x[3])
            file.write(";")
            file.write(x[4])
            file.write(";")
            file.write(x[5])
            file.write("\n")
    file.close()
    return


def create_file_cve_reverse(cve_data, fn):
    file = open(fn, "w")
    if not cve_data:
        file.write("NO CVE\n")
    else:
        file.write("System Name;CVE\n")
        for x in cve_data:
            file.write(x[0])
            file.write(";")
            file.write(x[1])
            file.write("\n")
    file.close()
    return


def logfile_present(s):
    # noinspection PyPep8
    try:
        file = open(s, 'w')
    except:
        msg = "Not a valid file: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)
    file.close()
    return s


######################################################################
# main
######################################################################

def main():
    parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter, description=('''\
         Usage:
         CVEReport.py 
                 
               '''))
    parser.add_argument("-c", "--cve", help="list of CVEs to be checked, comma delimeted, no spaces", required=True)
    parser.add_argument("-r", "--reverse", action="store_true", default=0,
                        help="list systems that have the CVE installed")
    parser.add_argument("-f", "--filename",
                        help="filename the data should be writen in. If no path is given it will be stored in directory where the script has been started. Mandatory",
                        required=True, type=logfile_present)
    parser.add_argument('--version', action='version', version='%(prog)s 0.0.1, October 20, 2017')
    args = parser.parse_args()
    smt.log_info("")
    smt.log_info(f"Start {datetime.datetime.now()}")
    smt.log_info("")
    smt.log_info(f"Given list of CVEs: {args.cve}")
    smt.log_info("")
    smt.suman_login()
    cve_split = []
    for i in args.cve.split(','):
        cve_split.append(i)

    cve_data_collected = []
    for cve in cve_split:
        if not args.reverse:
            # noinspection PyPep8
            try:
                cve_list = smt.client.audit.listSystemsByPatchStatus(smt.session, cve, ["AFFECTED_PATCH_INAPPLICABLE",
                                                                                        "AFFECTED_PATCH_APPLICABLE"])
            except:
                cve_list = []
            if not cve_list:
                smt.log_warning(f"Given CVE {cve} does not exist.")
                break
            else:
                smt.log_info(f"Processing CVE {cve}.")
            for cve_system in cve_list:
                cve_data = []
                try:
                    cve_data.append(smt.client.system.getName(smt.session, cve_system.get("system_id")).get("name"))
                except:
                    smt.log_error(f'unable to get hostname for system with ID {cve_system.get("system_id")}')
                    break
                cve_data.append(cve)
                adv_list = ""
                pack_list = ""
                for adv in cve_system.get('errata_advisories'):
                    if adv_list:
                        adv_list = adv_list + ", " + adv
                    else:
                        adv_list = adv
                    # noinspection PyPep8
                    try:
                        cve_packages = smt.client.errata.listPackages(smt.session, adv)
                    except:
                        print("unable to find packages")
                    for package in cve_packages:
                        pack = package.get('name') + "-" + package.get('version') + "-" + package.get(
                            'release') + "-" + package.get('arch_label')
                        if pack_list:
                            pack_list = pack_list + ", " + pack
                        else:
                            pack_list = pack
                cve_data.append(adv_list)
                cve_data.append(cve_system.get('patch_status'))
                chan_list = ""
                for chan in cve_system.get("channel_labels"):
                    if chan_list:
                        chan_list = chan_list + ", " + chan
                    else:
                        chan_list = chan
                cve_data.append(chan_list)
                cve_data.append(pack_list)
                cve_data_collected.append(cve_data)
            smt.log_info("Completed.")
        else:
            try:
                cve_list = smt.client.audit.listSystemsByPatchStatus(smt.session, cve, ["NOT_AFFECTED", "PATCHED"])
            except:
                cve_list = []
            if not cve_list:
                smt.log_warning("Given CVE %s does not exist." % cve)
                break
            else:
                smt.log_info("Processing CVE %s." % cve)
            for cve_system in cve_list:
                cve_data = []
                try:
                    cve_data.append(smt.client.system.getName(smt.session, cve_system.get("system_id")).get("name"))
                except:
                    smt.log_error("unable to get hostname for system with ID %s" % cve_system.get("system_id"))
                    break
                cve_data.append(cve)
                cve_data_collected.append(cve_data)
            smt.log_info("Completed.")
    if not args.reverse:
        create_file_cve(cve_data_collected, args.filename)
    else:
        create_file_cve_reverse(cve_data_collected, args.filename)
    smt.log_info(f"Result can be found in file {args.filename}")
    smt.suman_logout()
    smt.close_program()


if __name__ == "__main__":
    SystemExit(main())
