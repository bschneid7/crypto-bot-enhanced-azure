# Enhanced AI Crypto Trading Bot - Deployment Guide

## 🚀 Quick Deployment to Azure

### Prerequisites
- Azure account with active subscription
- GitHub account
- Binance API keys (for live trading)

### Step 1: Create GitHub Repository
1. Create a new **private** repository on GitHub
2. Upload all files from this directory to the repository
3. Push to the `main` branch

### Step 2: Configure GitHub Secrets
Go to your repository → Settings → Secrets and variables → Actions

Add these secrets:
- `AZURE_CREDENTIALS` - Azure service principal JSON
- `REGISTRY_USERNAME` - Azure Container Registry username
- `REGISTRY_PASSWORD` - Azure Container Registry password
- `BINANCE_API_KEY` - Your Binance API key
- `BINANCE_SECRET_KEY` - Your Binance secret key

### Step 3: Get Azure Credentials
```bash
# Create service principal
az ad sp create-for-rbac --name "enhanced-trading-bot-sp" \
  --role contributor \
  --scopes /subscriptions/$(az account show --query id --output tsv)/resourceGroups/bot-monitoring-rg \
  --sdk-auth

# Get registry credentials
az acr credential show --name botmonitorregistry
```

### Step 4: Deploy
1. Push any change to the `main` branch
2. GitHub Actions will automatically deploy to Azure
3. Check the Actions tab for deployment progress

### Step 5: Access Your Bot
After successful deployment:
- **Dashboard**: `http://[PUBLIC_IP]:8080`
- **API**: `http://[PUBLIC_IP]:8080/api/metrics`
- **Health**: `http://[PUBLIC_IP]:8080/health`

## 🔧 Manual Deployment (Alternative)

If GitHub Actions fails, you can deploy manually:

```bash
# Build and push image
docker build -t botmonitorregistry.azurecr.io/enhanced-trading-bot:latest .
docker push botmonitorregistry.azurecr.io/enhanced-trading-bot:latest

# Deploy container
az container create --resource-group bot-monitoring-rg --file azure-deploy.yml

```

## 📊 Monitoring Integration

### Update Monitoring System
Your existing Azure monitoring system needs to be updated to track the new bot:

1. Update the monitoring script URL to point to your new bot
2. Redeploy the monitoring system
3. Verify monitoring is working

### Expected Monitoring Behavior
- Health checks every 3 minutes
- Automatic restart on failure
- Email alerts for critical issues
- Performance tracking

## 🔍 Troubleshooting

### Common Issues
1. **Docker registry errors**: Wait a few minutes and retry
2. **Container won't start**: Check environment variables
3. **API errors**: Verify Binance API keys are correct
4. **Monitoring not working**: Update monitoring system URL

### Useful Commands
```bash
# Check container status
az container show --resource-group bot-monitoring-rg --name enhanced-trading-bot

# View logs
az container logs --resource-group bot-monitoring-rg --name enhanced-trading-bot

# Restart container
az container restart --resource-group bot-monitoring-rg --name enhanced-trading-bot

# Delete container
az container delete --resource-group bot-monitoring-rg --name enhanced-trading-bot
```

## 💰 Cost Optimization

### Resource Configuration
- **CPU**: 1.0 cores (adjustable)
- **Memory**: 1.0 GB (adjustable)
- **Estimated Cost**: $3-6/month

### Cost Monitoring
- Set up Azure cost alerts
- Monitor resource usage
- Optimize based on actual needs

## 🔐 Security Best Practices

### API Keys
- Store in GitHub Secrets (never in code)
- Use secure environment variables
- Rotate keys regularly

### Network Security
- Container runs on public IP (required for monitoring)
- Consider Azure Virtual Network for enhanced security
- Monitor access logs

## 📈 Performance Optimization

### Scaling
- Monitor CPU and memory usage
- Adjust resources as needed
- Consider multiple instances for high availability

### Algorithm Performance
- Monitor trading performance
- Adjust algorithm parameters
- Review logs for optimization opportunities

## 🎯 Next Steps

1. **Deploy the bot** using this guide
2. **Update monitoring system** to track new bot
3. **Test all functionality** before live trading
4. **Monitor performance** and optimize as needed
5. **Set up alerts** for critical issues

---

**⚠️ Important**: This bot executes real trades with real money. Test thoroughly in a safe environment before enabling live trading.

