from glob import glob
from insights.client.archive import InsightsArchive
from insights.client.connection import InsightsConnection
from insights.client.constants import InsightsConstants as constants
from insights.client.utilities import determine_hostname
from logging import getLogger
from platform import linux_distribution
from re import findall
from sys import exit
from insights.util.subproc import call
import os
import six

NONCOMPLIANT_STATUS = 2
COMPLIANCE_CONTENT_TYPE = 'application/vnd.redhat.compliance.something+tgz'
POLICY_FILE_LOCATION = '/usr/share/xml/scap/ssg/content/'
REQUIRED_PACKAGES = ['scap-security-guide', 'openscap-scanner', 'openscap']
logger = getLogger(__name__)


class ComplianceClient:
    def __init__(self, config):
        self.config = config
        self.conn = InsightsConnection(config)
        self.hostname = determine_hostname()
        self.archive = InsightsArchive(config)

    def oscap_scan(self):
        self._assert_oscap_rpms_exist()
        initial_profiles = self.get_initial_profiles()
        matching_os_profiles = self.get_profiles_matching_os()
        profiles = self.profile_union_by_ref_id(matching_os_profiles, initial_profiles)
        if not profiles:
            logger.error("System is not associated with any profiles. Assign profiles using the Compliance web UI.\n")
            exit(constants.sig_kill_bad)
        for profile in profiles:
            self.run_scan(
                profile['attributes']['ref_id'],
                self.find_scap_policy(profile['attributes']['ref_id']),
                '/var/tmp/oscap_results-{0}.xml'.format(profile['attributes']['ref_id']),
                tailoring_file_path=self.download_tailoring_file(profile)
            )

        return self.archive.create_tar_file(), COMPLIANCE_CONTENT_TYPE

    def download_tailoring_file(self, profile):
        if ('tailored' not in profile['attributes'] or profile['attributes']['tailored'] is False or
                ('os_minor_version' in profile['attributes'] and profile['attributes']['os_minor_version'] != self.os_minor_version())):
            return None

        # Download tailoring file to pass as argument to run_scan
        logger.debug(
            "Policy {0} is a tailored policy. Starting tailoring file download...".format(profile['attributes']['ref_id'])
        )
        tailoring_file_path = "/var/tmp/oscap_tailoring_file-{0}.xml".format(profile['attributes']['ref_id'])
        response = self.conn.session.get(
            "https://{0}/compliance/profiles/{1}/tailoring_file".format(self.config.base_url, profile['id'])
        )
        logger.debug("Response code: {0}".format(response.status_code))
        if response.content is None:
            logger.info("Problem downloading tailoring file for {0} to {1}".format(profile['attributes']['ref_id'], tailoring_file_path))
            return None

        with open(tailoring_file_path, mode="w+b") as f:
            f.write(response.content)
            logger.info("Saved tailoring file for {0} to {1}".format(profile['attributes']['ref_id'], tailoring_file_path))

        logger.debug("Policy {0} tailoring file download finished".format(profile['attributes']['ref_id']))

        return tailoring_file_path

    def get_profiles(self, search):
        response = self.conn.session.get("https://{0}/compliance/profiles".format(self.config.base_url),
                                         params={'search': search})
        logger.debug("Content of the response: {0} - {1}".format(response,
                                                                 response.json()))
        if response.status_code == 200:
            return (response.json().get('data') or [])
        else:
            return []

    def get_initial_profiles(self):
        return self.get_profiles('system_names={0} canonical=false external=false'.format(self.hostname))

    def get_profiles_matching_os(self):
        return self.get_profiles('system_names={0} canonical=false os_minor_version={1}'.format(self.hostname, self.os_minor_version()))

    def profile_union_by_ref_id(self, prioritized_profiles, merged_profiles):
        profiles = dict((p['attributes']['ref_id'], p) for p in merged_profiles)
        profiles.update(dict((p['attributes']['ref_id'], p) for p in prioritized_profiles))

        return list(profiles.values())

    def os_release(self):
        _, version, _ = linux_distribution()
        return version

    def os_major_version(self):
        return findall("^[6-8]", self.os_release())[0]

    def os_minor_version(self):
        return findall("\d+$", self.os_release())[0]

    def profile_files(self):
        return glob("{0}*rhel{1}*.xml".format(POLICY_FILE_LOCATION, self.os_major_version()))

    def find_scap_policy(self, profile_ref_id):
        grepcmd = 'grep ' + profile_ref_id + ' ' + ' '.join(self.profile_files())
        if not six.PY3:
            grepcmd = grepcmd.encode()
        rc, grep = call(grepcmd, keep_rc=True)
        if rc:
            logger.error('XML profile file not found matching ref_id {0}\n{1}\n'.format(profile_ref_id, grep))
            return None
        filenames = findall('/usr/share/xml/scap/.+xml', grep)
        if not filenames:
            logger.error('No XML profile files found matching ref_id {0}\n{1}\n'.format(profile_ref_id, ' '.join(filenames)))
            exit(constants.sig_kill_bad)
        return filenames[0]

    def build_oscap_command(self, profile_ref_id, policy_xml, output_path, tailoring_file_path):
        command = 'oscap xccdf eval --profile ' + profile_ref_id
        if tailoring_file_path:
            command += ' --tailoring-file ' + tailoring_file_path
        command += ' --results ' + output_path + ' ' + policy_xml
        return command

    def run_scan(self, profile_ref_id, policy_xml, output_path, tailoring_file_path=None):
        if policy_xml is None:
            return
        logger.info('Running scan for {0}... this may take a while'.format(profile_ref_id))
        env = os.environ.copy()
        env.update({'TZ': 'UTC'})
        oscap_command = self.build_oscap_command(profile_ref_id, policy_xml, output_path, tailoring_file_path)
        if not six.PY3:
            oscap_command = oscap_command.encode()
        rc, oscap = call(oscap_command, keep_rc=True, env=env)
        if rc and rc != NONCOMPLIANT_STATUS:
            logger.error('Scan failed')
            logger.error(oscap)
            exit(constants.sig_kill_bad)
        else:
            self.archive.copy_file(output_path)

    def _assert_oscap_rpms_exist(self):
        rpmcmd = 'rpm -qa ' + ' '.join(REQUIRED_PACKAGES)
        if not six.PY3:
            rpmcmd = rpmcmd.encode()
        rc, rpm = call(rpmcmd, keep_rc=True)
        if rc:
            logger.error('Tried running rpm -qa but failed: {0}.\n'.format(rpm))
            exit(constants.sig_kill_bad)
        else:
            if len(rpm.strip().split('\n')) < len(REQUIRED_PACKAGES):
                logger.error('Missing required packages for compliance scanning. Please ensure the following packages are installed: {0}\n'.format(', '.join(REQUIRED_PACKAGES)))
                exit(constants.sig_kill_bad)
