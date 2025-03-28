## 📌 **Manual: Running the Project Locally**

### Step 1: Install Required Software

- **Git**: [Download Git](https://git-scm.com/downloads) and install it.
- **Python 3.10**: Download from [python.org](https://www.python.org/downloads/release/python-3100/) and install.
- **Node.js (LTS)**: Download from [nodejs.org](https://nodejs.org/en/) and install.
- **Docker Desktop**: Download from [docker.com](https://docs.docker.com/get-docker/) and install.
- **Docker Compose**: Included with Docker Desktop, download from [docker.com](https://docs.docker.com/desktop/install/windows-install/) and install.
- **PostgreSQL**: Optional (Docker-compose already includes PostgreSQL).
- **Redis**: Optional (Docker-compose already includes Redis).

---

## Running the Project Locally

### Step 1: Clone the Repository
```sh
git clone <your-github-repo-url>
cd BillsTracker
```

### Step 2: Configure Environment Variables
Create `.env` files (never commit these files to GitHub):

**Backend** (`backend/.env`):
```env
DATABASE_URL=postgresql://user:password@db:5432/billsdb
REDIS_URL=redis://redis:6379/0
GOOGLE_CLIENT_ID=<your-google-client-id>
GOOGLE_CLIENT_SECRET=<your-google-client-secret>
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
JWT_SECRET=<generate-a-secure-random-secret>
AZURE_OPENAI_ENDPOINT=<your-azure-openai-endpoint>
AZURE_OPENAI_KEY=<your-azure-openai-key>
AZURE_OPENAI_API_VERSION=2023-10-01-preview
AZURE_OPENAI_ENGINE=<your-azure-openai-engine-name>
AZURE_BLOB_CONNECTION_STRING=<your-azure-blob-connection-string>
AZURE_BLOB_CONTAINER=<your-container-name>
FRONTEND_URL=http://localhost:3000
REDIS_URL=redis://redis:6379/0
DATABASE_URL=postgresql://user:password@db:5432/billsdb
```

**Important:**  
- **Never commit `.env` files or secrets to GitHub.**  
- Use `.gitignore` to exclude `.env`.

### Step 2: Install Docker Desktop
- Download and install Docker Desktop from [docker.com](https://docs.docker.com/get-docker/).

### Step 2: Build and Run Backend & Frontend
Navigate to the backend directory and run Docker Compose:
```sh
cd backend
docker-compose up --build
```

This command will:
- Build and run the backend API at `http://localhost:8000`.
- Run PostgreSQL database and Redis.
- Run Celery worker for background tasks.
- Build and run the frontend at `http://localhost:3000`.

### Step 2: Access the Application
- Open your browser and navigate to `http://localhost:3000`.
- Click "Sign in with Google" to authenticate.

### Step 2: Testing the Application
- After login, the frontend will redirect you to Google's OAuth page.
- After successful login, you'll be redirected back to the frontend dashboard.
- Click "Sync Bills" to trigger the Gmail synchronization task.
- Bills will appear in your dashboard after processing.

---

## Deploying the Project to Azure

### Step 1: Prerequisites
- Create an [Azure account](https://azure.microsoft.com/free/).
- Install [Azure CLI](https://docs.microsoft.com/cli/azure/install-azure-cli).
- Install [Docker Desktop](https://docs.docker.com/get-docker/).

### Step 2: Azure CLI Setup
Install Azure CLI from [here](https://docs.microsoft.com/cli/azure/install-azure-cli).

Login to Azure:
```sh
az login
```

### Step 2: Create Azure Resources
- **Resource Group**:
```sh
az group create --name BillsTrackerRG --location eastus
```

- **Azure Container Registry (ACR)**:
```sh
az acr create --resource-group BillsTrackerRG --name billstrackeracr --sku Basic
```

- **Azure Database for PostgreSQL**:
```sh
az postgres flexible-server create --resource-group  gmail-bill-scanner-rg --name billsdb --admin-user <dbuser> --admin-password <secure-password>
```

- **Azure Redis Cache**:
```sh
az redis create --name billsredis --resource-group  gmail-bill-scanner-rg --location eastus --sku Basic --vm-size c0
```

- **Azure Blob Storage**:
```sh
az storage account create --name yuvalnbillsstorage --resource-group gmail-bill-scanner-rg
 --location eastus --sku Standard_LRS
az storage container create --name billscontainer --account-name yuvalnbillsstorage
```

- **Azure OpenAI Service**:
  - Create via Azure Portal, note endpoint, API key, and deployment name.

- **Azure Key Vault** (for secure secrets storage):
```sh
az keyvault create --name BillscannersKeyVault --resource-group  gmail-bill-scanner-rg --location eastus
```

Store secrets securely in Key Vault:
```sh
az keyvault secret set --vault-name BillscannersKeyVault --name GOOGLE-CLIENT-ID --value "76690247848-of8kad73k8qr4eqa9immidpqoledkrgt.apps.googleusercontent.com"
az keyvault secret set --vault-name BillscannersKeyVault --name GOOGLE-CLIENT-SECRET --value "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"
az keyvault secret set --vault-name BillscannersKeyVault --name JWT-SECRET --value "p6nPA0mFOFxck567sz86t5Nvm9N3hfaF_ENdy8tRdo"
az keyvault secret set --vault-name BillscannersKeyVault --name AZURE-OPENAI-KEY --value "DBVv3lGCTjANORSUtR7LX2dAKB6c4V2i8vbGCNveN8p6s7tkUkz9JQQJ99BCACYeBjFXJ3w3AAABACOGZ4I5"
az keyvault secret set --vault-name BillscannersKeyVault --name AZURE-BLOB-CONNECTION-STRING --value "DefaultEndpointsProtocol=https;AccountName=yuvalnbillsstorage;AccountKey=KzviChVnmTPGH0HHXIaoHUbzSka+SM0SGkqAfpJdyRRfHs8w2sGEuVeuyp72aBQB4MSp/8EInidh+AStBTqpRw==;EndpointSuffix=core.windows.net"
```

### Step 3: Configure GitHub Actions for CI/CD
- In GitHub, navigate to your repo → Settings → Secrets and add Azure credentials as secrets.
- Create GitHub Actions workflow (`.github/workflows/deploy.yml`) to build Docker images and push to ACR.

Example workflow:
```yaml
name: Deploy to Azure

on:
  push:
    branches: [main]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - uses: azure/docker-login@v1
      with:
        login-server: <your-acr>.azurecr.io
        username: ${{ secrets.ACR_USERNAME }}
        password: ${{ secrets.ACR_PASSWORD }}

    - run: |
        docker build -t <your-acr>.azurecr.io/backend:latest ./backend
        docker push <your-acr>.azurecr.io/backend:latest
        docker build -t <your-acr>.azurecr.io/frontend:latest ./frontend
        docker push <your-acr>.azurecr.io/frontend:latest

    - uses: azure/k8s-set-context@v3
      with:
        kubeconfig: ${{ secrets.KUBE_CONFIG }}

    - run: |
        kubectl apply -f backend/k8s/backend-deployment.yaml
```

### Step 4: Deploy to Azure Kubernetes Service (AKS)
- Create AKS cluster:
```sh
az aks create --resource-group BillsTrackerRG --name BillsCluster --node-count 2 --generate-ssh-keys
```

- Connect ACR to AKS:
```sh
az aks update -n <your-aks-name> -g BillsTrackerRG --attach-acr <your-acr>
```

- Create Kubernetes secrets from Azure Key Vault (use Azure Key Vault Provider for Secrets Store CSI Driver).

- Deploy your application:
```sh
kubectl apply -f backend/k8s/backend-deployment.yaml
```

### Step 4: Accessing Your Application
- Expose your backend using Azure Load Balancer or Application Gateway.
- Configure DNS and SSL certificates if needed.

---

## Security Best Practices
- **Never store secrets or keys in your GitHub repository.**
- Always use environment variables or Azure Key Vault for sensitive data.
- Ensure `.env` files are added to `.gitignore`.

---

## Testing the Application
- **Local Testing**: Use Postman or browser to test API endpoints at `http://localhost:8000`.
- **Frontend Testing**: Open browser at `http://localhost:3000`.
- **Cloud Testing**: After deployment, access your frontend URL provided by Azure.

---

This manual is tailored specifically to your project structure and files, ensuring secure handling of sensitive information and proper integration with Azure services.

Ynaor: you wrote the the .env file should contain also AZURE_BLOB_CONNECTION_STRING=<your-azure-blob-connection-string>
AZURE_BLOB_CONTAINER=<your-container-name>

meaning the local testing is using the azure blob also?

GitHub Copilot: Yes, based on the provided project structure and the fields in your `Bill` model (specifically the `blob_name` field), your application is designed to store and retrieve files (such as bill attachments or PDFs) using Azure Blob Storage—even during local testing.

### Why Azure Blob Storage Locally?

- Your project likely uses Azure Blob Storage as a central storage solution for files, ensuring consistency between local and cloud environments.
- Using Azure Blob Storage locally simplifies development and testing, as you don't need to maintain separate storage solutions for local and cloud environments.

### Recommended Approach for Local Testing:

You have two main options:

#### Option 1: Use Azure Blob Storage (Recommended)

- **Pros**:  
  - Consistent behavior between local and cloud environments.
  - Easier to debug and test real-world scenarios.
- **Cons**:  
  - Requires internet connectivity.
  - Slightly slower due to network latency.

If you choose this option, your `.env` file should indeed contain:

```env
AZURE_BLOB_CONNECTION_STRING=<your-azure-blob-connection-string>
AZURE_BLOB_CONTAINER=<your-container-name>
```

#### Option 2: Use Local Storage (Alternative)

If you prefer not to depend on Azure during local testing, you can implement a local storage solution (e.g., saving files to a local directory):

- **Pros**:  
  - Faster file operations.
  - No dependency on Azure or internet connectivity.
- **Cons**:  
  - Additional code complexity (you'll need to implement logic to switch between local and Azure storage).
  - Potential differences between local and cloud environments.

If you choose this option, you would need to modify your code to handle local file storage during development and Azure Blob Storage in production.

---

### Recommended Best Practice:

For simplicity and consistency, it's common and recommended to use Azure Blob Storage even during local testing. Just ensure:

- You use a dedicated Azure Blob Storage container specifically for development/testing purposes.
- You never commit your Azure connection strings or keys to your GitHub repository (always use `.env` files and `.gitignore`).

This approach ensures your local environment closely mirrors your production environment, reducing potential issues when deploying to Azure.