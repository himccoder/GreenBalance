# 🌱 Green CDN - Carbon-Aware Load Balancing

Routes traffic to servers in regions with cleaner energy using real-time carbon data.

## 📁 Essential Files (Only 4!)

1. **`.env`** - Your WattTime API credentials (you already have this)
2. **`docker-compose.yml`** - Runs everything (3 servers + load balancer + carbon controller)
3. **`haproxy.cfg`** - Load balancer settings (you already have this)
4. **`carbon_controller.py`** - Gets carbon data and updates server weights

**Optional:** `test_green_cdn.py` - Test script to verify it's working

## 🚀 How to Run

Just 2 commands:

```powershell
# Start everything
docker-compose up -d

# Test it works
python test_green_cdn.py
```

That's it!

## 📊 Monitoring

- **Load Balancer**: http://localhost
- **HAProxy Stats Dashboard**: http://localhost:8404
- **Carbon Controller Logs**: `docker logs -f carbon-controller`

## 🌍 How It Works

1. **Carbon Controller** fetches real-time carbon intensity data from WattTime API for different US regions:
   - **US West (CAISO_NP)**: California - typically high renewable energy
   - **US Central (ERCOT)**: Texas - moderate renewable energy  
   - **US East (PJM)**: Mid-Atlantic - lower renewable energy

2. **Weight Calculation**: Servers in regions with lower carbon intensity get higher weights (more traffic)

3. **Dynamic Updates**: HAProxy weights are updated every 5 minutes based on real carbon data

## 🛠️ Configuration

The system maps each server to a specific carbon intensity region:

| Server | Region Code | Location | Typical Carbon Profile |
|--------|-------------|----------|----------------------|
| s1 | CAISO_NP | US West | Low (high renewables) |
| s2 | ERCOT | US Central | Moderate |
| s3 | PJM | US East | Higher (more fossil) |

## 🧪 Testing

Run the test suite to verify load balancing:
```bash
python test_green_cdn.py
```

## 🛑 Cleanup

Stop all services:
```bash
docker-compose down --remove-orphans
```

All Containerized on mynetwork:
┌─────────────────────────────────────────┐
│  Docker Bridge Network: mynetwork      │
│                                         │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐ │
│  │  web1   │  │  web2   │  │  web3   │ │
│  │container│  │container│  │container│ │
│  └─────────┘  └─────────┘  └─────────┘ │
│       ▲            ▲            ▲      │
│       └────────────┼────────────┘      │
│                    │                   │
│            ┌─────────────┐              │
│            │   HAProxy   │              │
│            │ (container) │              │
│            └─────────────┘              │
└─────────────────┬───────────────────────┘
                  │
            Host Ports 80 & 8404


graph TD
    A[Client Request] --> B[HAProxy Load Balancer]
    
    B --> C[Server 1<br/>US West California<br/>Weight: Dynamic]
    B --> D[Server 2<br/>US Central Texas<br/>Weight: Dynamic] 
    B --> E[Server 3<br/>US East Mid-Atlantic<br/>Weight: Dynamic]
    
    F[Carbon Controller] --> G[WattTime API v3]
    F --> H[HAProxy Admin Socket]
    
    G --> I[Real Carbon Data<br/>CAISO_NORTH<br/>Free Account Access]
    G --> J[Simulated Carbon Data<br/>Texas & PJM regions<br/>Realistic patterns]
    
    I --> K[Carbon Intensity<br/>lbs CO2/MWh]
    J --> K
    
    K --> L[Weight Calculation Algorithm<br/>Lower Carbon = Higher Weight]
    L --> M[Update HAProxy Weights<br/>Via Admin Socket]
    M --> H
    
    H --> N[Dynamic Traffic Distribution<br/>More traffic to greener servers]
    N --> B
    
    O[Every 5 Minutes] --> F
    
    style C fill:#90EE90
    style D fill:#FFE4B5  
    style E fill:#FFB6C1
    style I fill:#90EE90
    style J fill:#E6E6FA
    style L fill:#87CEEB




    FOR each server region:
    1. Get carbon intensity (lbs CO2/MWh)
       - Server 1: REAL data from WattTime API (CAISO_NORTH)
       - Server 2&3: SIMULATED data (realistic patterns)
    
    2. Calculate "green score" = Invert carbon intensity
       - Lower carbon intensity = Higher green score
    
    3. Convert green score to HAProxy weight (1-256)
       - Higher green score = Higher weight = More traffic
    
    4. Update HAProxy via admin socket
    
    5. Repeat every 5 minutes
   
   
   docker compose down
   docker compose up -d
   Start-Sleep 15; docker logs --tail 25 carbon-controller




Part 1: Start-Sleep 15
What it does: Pauses execution for 15 seconds
Why we need it: Gives the containers time to fully start up and initialize
Think of it as: "Wait 15 seconds before doing the next thing"
Part 2: ;
What it does: Separates two commands in PowerShell
Means: "Do the first command, then do the second command"
Like saying: "First wait 15 seconds, THEN check the logs"
Part 3: docker logs --tail 25 carbon-controller
docker logs: Get the log output from a Docker container
--tail 25: Only show the last 25 lines (most recent entries)
carbon-controller: The name of our container we want logs from