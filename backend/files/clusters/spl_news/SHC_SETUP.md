# Splunk Search Head Cluster (SHC) Setup Instructions
# Cluster: spl_news
# Generated: 2025-08-23T21:17:58.386153

## Overview
This document provides step-by-step instructions to set up a Search Head Cluster (SHC) for the spl_news cluster.

## Prerequisites
- All target hosts have Splunk Enterprise installed and running
- Network connectivity between deployer and search heads
- SSH access to all hosts as root user
- Splunk admin credentials (default: admin/changeme)

## Step 1: Configure Deployer
The deployer configuration is already created in the cluster files. You need to:

1. Copy the deployer configuration to your deployer host
2. Place it in `/opt/splunk/etc/shcluster/apps/siemply_spl_news_deployer/`
3. Restart Splunk on the deployer

## Step 2: Configure Search Heads
For each search head:

1. Copy the search head configuration to `/opt/splunk/etc/apps/siemply_spl_news_sh/`
2. Replace template variables:
   - `{SERVER_NAME}` → `sh-<IP_ADDRESS>`
   - `{DEPLOYER_IP}` → `<DEPLOYER_IP_ADDRESS>`
   - `{MGMT_URI}` → `https://<SEARCH_HEAD_IP>:8089`
3. Restart Splunk on each search head

## Step 3: Bootstrap the Cluster
On the first search head:

```bash
sudo -u splunk /opt/splunk/bin/splunk init shcluster-config \
  -auth admin:changeme \
  -mgmt_uri https://<FIRST_SH_IP>:8089 \
  -replication_port 8181 \
  -replication_factor 2 \
  -conf_deploy_fetch_url https://<DEPLOYER_IP>:8089 \
  -secret dTPr!t0AzG4o@VJ96qzlj7IzRLKdmgGK \
  -shcluster_label sh-spl_news
```

Restart the first search head.

## Step 4: Join Other Search Heads
On each additional search head:

```bash
sudo -u splunk /opt/splunk/bin/splunk init shcluster-config \
  -auth admin:changeme \
  -mgmt_uri https://<SH_IP>:8089 \
  -replication_port 8181 \
  -secret dTPr!t0AzG4o@VJ96qzlj7IzRLKdmgGK \
  -shcluster_label sh-spl_news
```

Restart each search head.

## Step 5: Elect Captain
On any search head:

```bash
sudo -u splunk /opt/splunk/bin/splunk bootstrap shcluster-captain \
  -servers_list "https://<SH1_IP>:8089,https://<SH2_IP>:8089" \
  -auth admin:changeme
```

## Step 6: Verify Cluster Status
Check cluster status on any search head:

```bash
sudo -u splunk /opt/splunk/bin/splunk show shcluster-status -auth admin:changeme
```

## Step 7: Connect to Indexers
On each search head, add indexers:

```bash
sudo -u splunk /opt/splunk/bin/splunk add search-server https://<INDEXER_IP>:8089 -auth admin:changeme
```

## Automation
You can also use the automated setup script:

```bash
cd backend/scripts
python3 setup_shcluster.py
```

## Troubleshooting
- Check Splunk logs: `sudo -u splunk /opt/splunk/bin/splunk list log`
- Verify network connectivity between hosts
- Ensure all template variables are properly replaced
- Check that replication port 8181 is not blocked by firewall

## Template Variables Reference
- `{SERVER_NAME}`: Hostname for the search head (e.g., sh-192.168.1.100)
- `{DEPLOYER_IP}`: IP address of the deployer host
- `{MGMT_URI}`: Management URI for the search head (e.g., https://192.168.1.100:8089)
- `{HOST_IP}`: IP address of the target host
- `{CLUSTER_NAME}`: Name of the cluster
