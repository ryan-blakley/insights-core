from insights.parsers.installed_rpms import InstalledRpms
from insights.parsers.satellite_version import Satellite6Version
from insights.combiners import satellite_version
from insights.combiners.satellite_version import SatelliteVersion, CapsuleVersion
from insights.parsers.ssl_certificate import RhsmKatelloDefaultCACert
from insights.parsers.rhsm_conf import RHSMConf
from insights.combiners.hostname import Hostname
from insights.parsers.hostname import Hostname as Hnf
from insights.tests import context_wrap
from insights import SkipComponent
import pytest
import doctest


installed_rpms_5 = """
satellite-branding-5.5.0.22-1.el6sat.noarch                 Wed May 18 14:50:17 2016
satellite-doc-indexes-5.6.0-2.el6sat.noarch                 Wed May 18 14:47:49 2016
satellite-repo-5.6.0.3-1.el6sat.noarch                      Wed May 18 14:37:34 2016
satellite-schema-5.6.0.10-1.el6sat.noarch                   Wed May 18 14:53:03 2016
satyr-0.16-2.el6.x86_64                                     Wed May 18 14:16:08 2016
scdb-1.15.8-1.el6sat.noarch                                 Wed May 18 14:48:14 2016
scl-utils-20120927-27.el6_6.x86_64                          Wed May 18 14:18:16 2016
SDL-1.2.14-6.el6.x86_64                                     Wed May 18 14:16:25 2016
"""

installed_rpms_60 = """
foreman-1.6.0.53-1.el7sat.noarch                            Wed May 18 14:16:25 2016
candlepin-0.9.23.11-1.el7.noarch                            Wed May 18 14:16:25 2016
katello-1.5.0.2-1.el7.noarch                                Wed May 18 14:16:25 2016
scl-utils-20120927-27.el6_6.x86_64                          Wed May 18 14:18:16 2016
SDL-1.2.14-6.el6.x86_64                                     Wed May 18 14:16:25 2016
"""

installed_rpms_61 = """
foreman-1.7.2.53-1.el7sat.noarch                            Wed May 18 14:16:25 2016
candlepin-0.9.49.11-1.el7.noarch                            Wed May 18 14:16:25 2016
katello-2.2.0.17-1.el7.noarch                               Wed May 18 14:16:25 2016
scl-utils-20120927-27.el6_6.x86_64                          Wed May 18 14:18:16 2016
SDL-1.2.14-6.el6.x86_64                                     Wed May 18 14:16:25 2016
"""

installed_rpms_62 = """
foreman-1.11.0.53-1.el7sat.noarch                           Wed May 18 14:16:25 2016
scl-utils-20120927-27.el7_6.x86_64                          Wed May 18 14:18:16 2016
SDL-1.2.14-6.el7.x86_64                                     Wed May 18 14:16:25 2016
satellite-6.2.0.11-1.el7sat.noarch                          Wed May 18 14:16:25 2016
"""

installed_rpms_62_cap = """
scl-utils-20120927-27.el7_6.x86_64                          Wed May 18 14:18:16 2016
SDL-1.2.14-6.el7.x86_64                                     Wed May 18 14:16:25 2016
satellite-capsule-6.2.0.11-1.el7sat.noarch                  Wed May 18 14:16:25 2016
"""

BOTH_SATELLITE_AND_SATELLITE_CAPSULE = """
scl-utils-20120927-27.el7_6.x86_64                          Wed May 18 14:18:16 2016
SDL-1.2.14-6.el7.x86_64                                     Wed May 18 14:16:25 2016
satellite-capsule-6.8.0.11-1.el7sat.noarch                  Wed May 18 14:16:25 2016
satellite-6.8.0.11-1.el7sat.noarch                          Wed May 18 14:16:25 2016
foreman.el7.x86_64                                          Wed May 18 14:16:25 2016
"""

RHSM_CONF_CDN = """
# Red Hat Subscription Manager Configuration File:

# Unified Entitlement Platform Configuration
[server]
# Server hostname:
hostname = subscription.rhsm.redhat.com

# Server prefix:
prefix = /subscription

# Server port:
port = 443

# Set to 1 to disable certificate validation:
insecure = 0

# Set the depth of certs which should be checked
# when validating a certificate
ssl_verify_depth = 3
"""

RHSM_CONF_NON_CDN = """
# Red Hat Subscription Manager Configuration File:

# Unified Entitlement Platform Configuration
[server]
# Server hostname:
hostname = abc.def.fg.com

# Server prefix:
prefix = /subscription

# Server port:
port = 443

# Set to 1 to disable certificate validation:
insecure = 0

# Set the depth of certs which should be checked
# when validating a certificate
ssl_verify_depth = 3
"""

RHSM_CONF_CDN_NO_HOSTNAME = """
# Red Hat Subscription Manager Configuration File:

# Unified Entitlement Platform Configuration
[server]
# Server hostname:
"""

HOSTNAME_1 = """
abc.def.fg.com
"""

HOSTNAME_2 = """
testsat.example.com
"""

KATELLO_DEFAULT_CA_ISSUER_OUPTUT_HIT = """
issuer= /C=US/ST=North Carolina/L=Raleigh/O=Katello/OU=SomeOrgUnit/CN=testsat.example.com
""".strip()

KATELLO_DEFAULT_CA_ISSUER_OUPTUT_NON_HIT = """
issuer= /C=US/ST=North Carolina/L=Raleigh/O=Katello/OU=SomeOrgUnit/CN=another.example.com
""".strip()


satellite_version_rb = """
COMMAND> cat /usr/share/foreman/lib/satellite/version.rb

module Satellite
  VERSION = "6.1.3"
end
"""

no_sat = """
scdb-1.15.8-1.el6sat.noarch                                 Wed May 18 14:48:14 2016
scl-utils-20120927-27.el6_6.x86_64                          Wed May 18 14:18:16 2016
SDL-1.2.14-6.el6.x86_64                                     Wed May 18 14:16:25 2016
"""

installed_rpms_6110 = """
foreman-1.7.2.61-1.el7sat.noarch                            Wed May 18 14:16:25 2016
candlepin-0.9.49.16-1.el7.noarch                            Wed May 18 14:16:25 2016
katello-2.2.0.19-1.el7.noarch                               Wed May 18 14:16:25 2016
scl-utils-20120927-27.el6_6.x86_64                          Wed May 18 14:18:16 2016
"""

installed_rpms_6111 = """
foreman-1.7.2.62-1.el7sat.noarch                            Wed May 18 14:16:25 2016
candlepin-0.9.49.19-1.el7.noarch                            Wed May 18 14:16:25 2016
katello-2.2.0.19-1.el7.noarch                               Wed May 18 14:16:25 2016
scl-utils-20120927-27.el6_6.x86_64                          Wed May 18 14:18:16 2016
"""

installed_rpms_611x_confilct = """
foreman-1.7.2.61-1.el7sat.noarch                            Wed May 18 14:16:25 2016
candlepin-0.9.54.10-1.el7.noarch                            Wed May 18 14:16:25 2016
katello-2.3.0.19-1.el7.noarch                               Wed May 18 14:16:25 2016
scl-utils-20120927-27.el6_6.x86_64                          Wed May 18 14:18:16 2016
"""


def test_get_sat5_version():
    rpms = InstalledRpms(context_wrap(installed_rpms_5))
    expected = ('satellite-schema-5.6.0.10-1.el6sat',
                '5.6.0.10', '1.el6sat', 5, 6)
    result = SatelliteVersion(rpms, None, None, None, None)
    assert result.major == expected[-2]
    assert result.minor == expected[-1]
    assert result.full == expected[0]
    assert result.release == expected[2]
    assert result.version == expected[1]


def test_get_sat61_version():
    rpms = InstalledRpms(context_wrap(installed_rpms_61))
    expected = ('6.1.7', '6.1.7', None, 6, 1)
    result = SatelliteVersion(rpms, None, None, None, None)
    assert result.major == expected[-2]
    assert result.minor == expected[-1]
    assert result.full == expected[0]
    assert result.release == expected[2]
    assert result.version == expected[1]

    sat = Satellite6Version(context_wrap(satellite_version_rb))
    expected = ('6.1.3', '6.1.3', None, 6, 1)
    result = SatelliteVersion(rpms, sat, None, None, None)
    assert result.major == expected[-2]
    assert result.minor == expected[-1]
    assert result.full == expected[0]
    assert result.release == expected[2]
    assert result.version == expected[1]

    rpms = InstalledRpms(context_wrap(installed_rpms_6110))
    expected = ('6.1.10', '6.1.10', None, 6, 1)
    result = SatelliteVersion(rpms, None, None, None, None)
    assert result.major == expected[-2]
    assert result.minor == expected[-1]
    assert result.full == expected[0]
    assert result.release == expected[2]
    assert result.version == expected[1]

    rpms = InstalledRpms(context_wrap(installed_rpms_6111))
    expected = ('6.1.11', '6.1.11', None, 6, 1)
    result = SatelliteVersion(rpms, None, None, None, None)
    assert result.major == expected[-2]
    assert result.minor == expected[-1]
    assert result.full == expected[0]
    assert result.release == expected[2]
    assert result.version == expected[1]


def test_get_sat60():
    rpms = InstalledRpms(context_wrap(installed_rpms_60))
    expected = ('6.0.8', '6.0.8', None, 6, 0)
    result = SatelliteVersion(rpms, None, None, None, None)
    assert result.major == expected[-2]
    assert result.minor == expected[-1]
    assert result.full == expected[0]
    assert result.release == expected[2]
    assert result.version == expected[1]


def test_get_sat61_version_both():
    rpms = InstalledRpms(context_wrap(installed_rpms_61))
    sat = Satellite6Version(context_wrap(satellite_version_rb))
    expected = ('6.1.3', '6.1.3', None, 6, 1)
    result = SatelliteVersion(rpms, sat, None, None, None)
    assert result.major == expected[-2]
    assert result.minor == expected[-1]
    assert result.full == expected[0]
    assert result.release == expected[2]
    assert result.version == expected[1]


def test_get_sat62_version():
    rpms = InstalledRpms(context_wrap(installed_rpms_62))
    expected = ('satellite-6.2.0.11-1.el7sat',
                '6.2.0.11', '1.el7sat', 6, 2)
    result = SatelliteVersion(rpms, None, None, None, None)
    assert result.major == expected[-2]
    assert result.minor == expected[-1]
    assert result.full == expected[0]
    assert result.version == expected[1]
    assert result.release == expected[2]


def test_get_sat62_capsule_version():
    rpms = InstalledRpms(context_wrap(installed_rpms_62_cap))
    expected = ('satellite-capsule-6.2.0.11-1.el7sat',
                '6.2.0.11', '1.el7sat', 6, 2)
    result = CapsuleVersion(rpms, None)
    assert result.major == expected[-2]
    assert result.minor == expected[-1]
    assert result.full == expected[0]
    assert result.version == expected[1]
    assert result.release == expected[2]


def test_no_sat_installed():
    rpms = InstalledRpms(context_wrap(no_sat))
    with pytest.raises(SkipComponent) as sc:
        SatelliteVersion(rpms, None, None, None, None)
    assert "Not a Satellite machine" in str(sc)

    rpms = InstalledRpms(context_wrap(no_sat))
    with pytest.raises(SkipComponent) as sc:
        CapsuleVersion(rpms, None)
    assert "Not a Satellite Capsule machine" in str(sc)

    rpms = InstalledRpms(context_wrap(installed_rpms_611x_confilct))
    with pytest.raises(SkipComponent) as sc:
        SatelliteVersion(rpms, None, None, None, None)
    assert "unable to determine Satellite version" in str(sc)


def test_both_pkgs():
    rpms = InstalledRpms(context_wrap(BOTH_SATELLITE_AND_SATELLITE_CAPSULE))
    rhsm_cdn = RHSMConf(context_wrap(RHSM_CONF_CDN))
    rhsm_not_cdn = RHSMConf(context_wrap(RHSM_CONF_NON_CDN))
    rhsm_without_hostname = RHSMConf(context_wrap(RHSM_CONF_CDN_NO_HOSTNAME))

    # satellite register to cdn
    result = SatelliteVersion(rpms, None, rhsm_cdn, None, None)
    assert result is not None
    assert result.version == '6.8.0.11'

    # not a satellite to cdn
    with pytest.raises(SkipComponent):
        SatelliteVersion(rpms, None, rhsm_not_cdn, None, None)

    # can not identify since hostname missed
    with pytest.raises(SkipComponent):
        SatelliteVersion(rpms, None, rhsm_without_hostname, None, None)

    # a capsule to cdn
    result = CapsuleVersion(rpms, rhsm_not_cdn)
    assert result is not None
    assert result.version == '6.8.0.11'

    # not a capsule to cdn
    with pytest.raises(SkipComponent):
        CapsuleVersion(rpms, rhsm_cdn)

    # satellite register to itself by cdn
    parser_hostname_hit = Hnf(context_wrap(HOSTNAME_1))
    parser_hostname_not_hit = Hnf(context_wrap(HOSTNAME_2))
    hostname_hit = Hostname(parser_hostname_hit, None, None, None)
    hostname_not_hit = Hostname(parser_hostname_not_hit, None, None, None)
    result = SatelliteVersion(rpms, None, rhsm_not_cdn, hostname_hit, None)
    assert result is not None
    assert result.version == '6.8.0.11'

    # not a satellite
    with pytest.raises(SkipComponent):
        SatelliteVersion(rpms, None, rhsm_not_cdn, hostname_not_hit, None)

    # a satellite which register to itself
    ca_cert_hit = RhsmKatelloDefaultCACert(context_wrap(KATELLO_DEFAULT_CA_ISSUER_OUPTUT_HIT))
    ca_cert_not_hit = RhsmKatelloDefaultCACert(context_wrap(KATELLO_DEFAULT_CA_ISSUER_OUPTUT_NON_HIT))
    SatelliteVersion(rpms, None, rhsm_not_cdn, hostname_not_hit, ca_cert_hit)
    assert result is not None
    assert result.version == '6.8.0.11'

    # not a satellite
    with pytest.raises(SkipComponent):
        SatelliteVersion(rpms, None, rhsm_not_cdn, hostname_not_hit, ca_cert_not_hit)


def test_doc_examples():
    sat_rpms = InstalledRpms(context_wrap(installed_rpms_62))
    cap_rpms = InstalledRpms(context_wrap(installed_rpms_62_cap))
    env = {
            'sat_ver': SatelliteVersion(sat_rpms, None, None, None, None),
            'cap_ver': CapsuleVersion(cap_rpms, None),
          }
    failed, total = doctest.testmod(satellite_version, globs=env)
    assert failed == 0
