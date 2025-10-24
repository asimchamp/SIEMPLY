"""
Splunk automation module
Contains Splunk Universal Forwarder installation and management functionality
"""

from .splunk_installer import install_splunk_uf, repair_splunk_permissions

__all__ = ['install_splunk_uf', 'repair_splunk_permissions'] 