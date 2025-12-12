# Deploying Jarqyn to Google Cloud (Compute Engine)

Since your project uses **SQLite** (a file-based database) and a **Telegram Bot** (polling mode), the simplest and most reliable way to deploy is using a **Virtual Machine (VM)** on Google Compute Engine.

This approach gives you a server that runs 24/7, keeping your bot alive and your database saved on the disk.

## Prerequisites
1.  A Google Cloud Project with billing enabled.
2.  [Google Cloud SDK (gcloud)](https://cloud.google.com/sdk/docs/install) installed on your computer (optional, but recommended).
    *   *Alternative*: You can do everything via the Google Cloud Console website.

---

## Step 1: Create a VM Instance

1.  Go to the **Google Cloud Console** > **Compute Engine** > **VM instances**.
2.  Click **Create Instance**.
3.  **Name**: `jarqyn-server`
4.  **Region**: Choose one close to you (e.g., `europe-west1` or `us-central1`).
5.  **Machine type**: `e2-micro` (part of Free Tier) or `e2-small` is enough for testing.
6.  **Boot disk**:
    *   Click "Change".
    *   Select **Ubuntu** (e.g., Ubuntu 22.04 LTS).
    *   Size: 10 GB (standard).
7.  **Firewall**: Check **Allow HTTP traffic** and **Allow HTTPS traffic**.
8.  Click **Create**.

## Step 2: Connect to the VM

1.  In the VM list, click the **SSH** button next to your new instance.
2.  A terminal window will open in your browser. This is your server's command line.

## Step 3: Install Docker & Docker Compose

Run these commands in the SSH terminal to install the necessary tools:

```bash
# Update package list
sudo apt-get update

# Install Docker
sudo apt-get install -y docker.io

# Start Docker and enable it to run on boot
sudo systemctl start docker
sudo systemctl enable docker

# Add your user to the docker group (avoids typing sudo for every docker command)
sudo usermod -aG docker $USER
```

*Note: You might need to close the SSH window and open it again for the group change to take effect.*

## Step 4: Transfer Your Code

You have two options: **Git** (recommended) or **SCP** (uploading files directly).

### Option A: Using Git (Easiest)
1.  Push your code to GitHub/GitLab.
2.  On the VM, clone it:
    ```bash
    git clone https://github.com/YOUR_USERNAME/Jarqyn.git
    cd Jarqyn
    ```

### Option B: Uploading Files (If no Git repo)
1.  On your **local computer**, open a terminal in your project folder (`Documents/Jarqyn`).
2.  Use `gcloud` to copy files (replace `INSTANCE_NAME` and `ZONE`):
    ```powershell
    # Copy the whole folder (excluding venv)
    gcloud compute scp --recurse . jarqyn-server:~/Jarqyn --zone=YOUR_ZONE
    ```

## Step 5: Configure Environment Variables

1.  Inside the server (SSH), go to your project folder:
    ```bash
    cd ~/Jarqyn
    ```
2.  Create/Edit the `.env` file for the bot:
    ```bash
    nano bot/.env
    ```
3.  Paste your keys (right-click to paste):
    ```env
    BOT_TOKEN=your_actual_bot_token_here
    API_URL=http://backend:8000/api/reports/
    ```
4.  Press `Ctrl+X`, then `Y`, then `Enter` to save.

5.  Do the same for the backend if it has an `.env` file:
    ```bash
    nano backend/.env
    ```
    (Paste `GEMINI_API_KEY` etc.)

## Step 6: Start the Application

1.  Run the application in "detached" mode (background):
    ```bash
    docker-compose up -d --build
    ```

2.  Check if it's running:
    ```bash
    docker-compose ps
    ```

## Step 7: Open the Firewall (Optional)

By default, your backend running on port `8000` is accessible *inside* the server (allowing the bot to talk to it), but **not** from the outside world (like your browser).

If you want to see the backend API docs (`/docs`) from your browser:
1.  Go to **VPC Network** > **Firewall** in Google Cloud Console.
2.  **Create Firewall Rule**.
3.  **Name**: `allow-8000`.
4.  **Targets**: `All instances in the network`.
5.  **Source IPv4 ranges**: `0.0.0.0/0`.
6.  **Protocols and ports**: tcp: `8000`.
7.  Click **Create**.

Now visit `http://YOUR_VM_EXTERNAL_IP:8000/docs`.

## Useful Commands

*   **View Logs**: `docker-compose logs -f`
*   **Stop App**: `docker-compose down`
*   **Update Code**:
    ```bash
    git pull
    docker-compose up -d --build
    ```
