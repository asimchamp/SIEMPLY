# Deployment Guide for spl_news

## Prerequisites
- All target hosts have Splunk Enterprise installed
- Network connectivity between cluster members
- SSL certificates configured (if SSL enabled)
- Firewall rules configured for cluster ports

## Deployment Steps

### 1. Cluster Manager
1. Copy `cm/default/` configuration to Cluster Manager host
2. Restart Splunk service
3. Verify cluster manager is running: `splunk show cluster-status`

### 2. Indexers
1. Copy `idx/default/` configuration to each Indexer host
2. Update `server.conf` with correct Cluster Manager URI
3. Restart Splunk service
4. Verify peer status: `splunk show cluster-peers`

### 3. Search Heads
1. Copy `sh/default/` configuration to each Search Head host
2. Update `server.conf` with correct Cluster Manager URI
3. Restart Splunk service
4. Verify search head status: `splunk show cluster-status`

### 4. Universal Forwarders
1. Copy `uf/default/` configuration to each Forwarder host
2. Update `outputs.conf` with correct Indexer Discovery settings
3. Restart Splunk service
4. Verify forwarding status: `splunk list forward-server`

## Verification Commands
- Cluster status: `splunk show cluster-status`
- Peer status: `splunk show cluster-peers`
- Search head status: `splunk show shcluster-status`
- Indexer discovery: `splunk list indexer-discovery`

## Troubleshooting
See TROUBLESHOOTING.md for common issues and solutions.
