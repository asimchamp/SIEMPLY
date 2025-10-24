"""
SIEMply Syslog Module
Provides syslog-ng installation and configuration functionality
"""

from .syslog_installer import install_syslog_ng

__all__ = ['install_syslog_ng'] 