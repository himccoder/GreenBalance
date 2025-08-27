# 🚀 Deploy Green CDN - Free Options

Choose your preferred free deployment method:

## 🎯 **Quick Demo Links**

Once deployed, share these URLs with others:

- **Main Dashboard**: `https://your-app.railway.app` (Weight Manager)
- **Weight Viewer**: `https://your-app.railway.app:5001` (Live weights)
- **HAProxy Stats**: `https://your-app.railway.app:8404/stats` (Load balancer stats)
- **Load Balancer**: `https://your-app.railway.app:80` (Test traffic)

---

## 🚂 **Option 1: Railway.app (RECOMMENDED)**

**Best for: Full deployment with custom domain**

### Step 1: Setup Railway Account
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login
```

### Step 2: Deploy Each Service
```bash
# Deploy Weight Manager (main app)
railway project new
railway up --service weight-manager

# Deploy Weight Viewer
railway service new weight-viewer
railway up --service weight-viewer

# Deploy HAProxy
railway service new haproxy
railway up --service haproxy
```

### Step 3: Configure Environment Variables
```bash
# Set environment variables in Railway dashboard
DATAPLANE_HOST=your-haproxy-url.railway.app
PYTHONUNBUFFERED=1
```

**💰 Cost**: FREE ($5/month credit covers small apps)
**⏱️ Setup Time**: 10 minutes
**🌐 Domain**: `your-app.up.railway.app`

---

## 🎨 **Option 2: Render.com**

**Best for: Simple web services**

### Step 1: Connect GitHub
1. Go to [render.com](https://render.com)
2. Connect your GitHub repository
3. Select "New Web Service"

### Step 2: Deploy Services
```yaml
# Use the provided render.yaml file
# Render will automatically detect and deploy all services
```

**💰 Cost**: FREE (750 hours/month)
**⏱️ Setup Time**: 5 minutes
**🌐 Domain**: `your-app.onrender.com`

---

## 🐙 **Option 3: GitHub Codespaces (Best for Demos)**

**Best for: Interactive demos and development**

### Step 1: Enable Codespaces
1. Push your code to GitHub
2. Click "Code" → "Codespaces" → "Create codespace"
3. Wait for environment to load

### Step 2: Auto-Start
```bash
# Services start automatically via .devcontainer/devcontainer.json
# All ports are forwarded and accessible via generated URLs
```

### Step 3: Share Demo
1. Click "Ports" tab in VS Code
2. Make ports public
3. Share the generated URLs

**💰 Cost**: FREE (60 hours/month)
**⏱️ Setup Time**: 2 minutes
**🌐 Access**: Generated GitHub URLs

---

## 🐋 **Option 4: Play with Docker (Instant)**

**Best for: Quick testing and demos**

### Step 1: One-Click Deploy
[![Try in PWD](https://raw.githubusercontent.com/play-with-docker/stacks/cff22438cb4195ace27f9b15784bbb497047afa7/assets/images/button.png)](https://labs.play-with-docker.com/?stack=https://raw.githubusercontent.com/your-username/greenCDN/main/docker-compose.yml)

### Step 2: Access Services
```bash
# Click on exposed ports in the PWD interface
# Ports 5000, 5001, 80, 8404 will be available
```

**💰 Cost**: FREE
**⏱️ Setup Time**: 30 seconds
**🌐 Access**: Temporary PWD URLs (4 hours)

---

## 🛠️ **Quick Local Testing**

Before deploying, test locally:

### Windows (PowerShell)
```powershell
.\scripts\playground.ps1
```

### Linux/Mac
```bash
make up
```

### Access Points
- Weight Manager: http://localhost:5000
- Weight Viewer: http://localhost:5001
- HAProxy Stats: http://localhost:8404/stats
- Load Balancer: http://localhost:80

---

## 🎯 **Recommended Flow**

1. **Start with GitHub Codespaces** for instant demo
2. **Deploy to Railway** for permanent public access
3. **Share the Railway URL** with others

## 📧 **Share Your Demo**

Once deployed, share these key URLs:

```
🌱 **Green CDN Demo**
📊 Dashboard: https://your-app.railway.app
👀 Live Weights: https://your-app.railway.app:5001
📈 HAProxy Stats: https://your-app.railway.app:8404/stats
🔄 Load Balancer: https://your-app.railway.app:80

Try the carbon-aware load balancing in action!
```

---

## 🆘 **Troubleshooting**

### Common Issues:
1. **Services not starting**: Check logs in platform dashboard
2. **Ports not accessible**: Ensure all ports are exposed in deployment config
3. **Inter-service communication**: Update service URLs in environment variables

### Support:
- Railway: [docs.railway.app](https://docs.railway.app)
- Render: [render.com/docs](https://render.com/docs)
- GitHub Codespaces: [docs.github.com/codespaces](https://docs.github.com/codespaces)
