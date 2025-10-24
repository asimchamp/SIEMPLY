# Troubleshooting Guide

## Common Issues

### 1. Cluster Manager Not Starting
- Check `server.conf` syntax
- Verify SSL certificates exist
- Check port 8089 is not blocked
- Review Splunk logs: `splunk list log`

### 2. Indexers Not Joining Cluster
- Verify Cluster Manager URI is correct
- Check network connectivity
- Verify `pass4SymmKey` matches
- Check SSL configuration

### 3. Search Heads Not Clustering
- Verify Deployer URI is correct
- Check Search Head Cluster configuration
- Verify `pass4SymmKey` matches
- Check SSL configuration

### 4. Forwarders Not Sending Data
- Verify Indexer Discovery configuration
- Check network connectivity to indexers
- Verify SSL configuration
- Check `outputs.conf` syntax

### 5. SSL/TLS Issues
- Verify certificate paths are correct
- Check certificate permissions
- Verify SSL versions are compatible
- Check cipher suite configuration

## Debug Commands
- `splunk list log` - List available logs
- `splunk show cluster-status` - Show cluster status
- `splunk show cluster-peers` - Show peer status
- `splunk show shcluster-status` - Show search head cluster status
- `splunk list indexer-discovery` - Show indexer discovery status

## Log Files
- `$SPLUNK_HOME/var/log/splunk/splunkd.log` - Main Splunk daemon log
- `$SPLUNK_HOME/var/log/splunk/clustering.log` - Clustering specific log
- `$SPLUNK_HOME/var/log/splunk/splunkd_access.log` - Access log

## Performance Tuning
- Adjust `max_threads` and `max_sockets` in `server.conf`
- Configure appropriate bucket sizes in `indexes.conf`
- Tune replication and search factors based on hardware
- Monitor cluster health and performance metrics
