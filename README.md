# **ublog 🚀**

A simple-but-powerful blogging platform where users can sign up, create topics, post content, and view their feeds. Built with Python (Flask), SQLite/Postgres, and Docker\!

## **Features**

* **Authentication:** Secure sign-up and login with reCAPTCHA.  
* **Roles:** Admin (Blue Cog), Moderator (Shiny Title), and standard Users.  
* **Profiles:** User profiles with Gravatar avatars and Follow systems.  
* **Blogs & Posts:** Create specific blogs, post inside them, and explore the global feed.  
* **Admin Dashboard:** Centralized control to manage users, blogs, and posts.

## **Local Setup Instructions**

1. **Clone the repository** (and ensure you have Docker installed).  
2. **Create your runner script.** Because the runner script contains sensitive keys, it is ignored by Git. Create a file named run.sh in the root directory and copy the template below into it.  
3. **Fill in your secrets** inside the run.sh script (like your Admin email and reCAPTCHA keys).  
4. Make the script executable:  
```bash
   chmod +x run.sh
```
5. Start the server:  
```bash
   ./run.sh
```
## **run.sh Template**

Copy this into your local run.sh file and replace the placeholder values with your actual data. DO NOT commit your real run.sh to version control\!
```bash
\#\!/bin/bash

echo "🧹 Cleaning up any old containers..."  
docker rm \-f ublog 2\>/dev/null

echo "🔨 Building the Docker image..."  
docker build \-t ublog:dev .

echo "🚀 Starting ublog with persistent volume..."  
docker run \-d \-p 8080:5000 \\  
  \-v ublog\_data:/app/src/instance \\  
  \-e ADMIN\_EMAIL="YOUR\_EMAIL\_HERE" \\  
  \-e RECAPTCHA\_SITE\_KEY="YOUR\_RECAPTCHA\_SITE\_KEY\_HERE" \\  
  \-e RECAPTCHA\_SECRET\_KEY="YOUR\_RECAPTCHA\_SECRET\_KEY\_HERE" \\  
  \--name ublog ublog:dev

echo "✅ ublog is now running\!"  
echo "👉 Open your browser to: http://localhost:8080"  
echo "------------------------------------------------"

\# Wait for input to kill the container  
while true; do  
    read \-p "Type 'k' and press Enter to kill the server (or anything else to ignore): " input  
      
    if \[ "$input" \== "k" \]; then  
        echo "🛑 Stopping and removing ublog..."  
        docker rm \-f ublog  
        echo "👋 All clean\! Server stopped."  
        break  
    else  
        echo "👍 Keeping the server running."  
    fi  
done  
```

## run the simple way
1. pull image
```bash
docker pull grishkkka/ublog
```
2. run

2.1. create run.sh
```bash
\#\!/bin/bash

echo "🧹 Cleaning up any old containers..."  
docker rm \-f ublog 2\>/dev/null

echo "🚀 Starting ublog with persistent volume..."  
docker run \-d \-p 8080:5000 \\  
  \-v ublog\_data:/app/src/instance \\  
  \-e ADMIN\_EMAIL="YOUR\_EMAIL\_HERE" \\  
  \-e RECAPTCHA\_SITE\_KEY="YOUR\_RECAPTCHA\_SITE\_KEY\_HERE" \\  
  \-e RECAPTCHA\_SECRET\_KEY="YOUR\_RECAPTCHA\_SECRET\_KEY\_HERE" \\  
  \--name ublog ublog:dev

echo "✅ ublog is now running\!"  
echo "👉 Open your browser to: http://localhost:8080"  
echo "------------------------------------------------"

\# Wait for input to kill the container  
while true; do  
    read \-p "Type 'k' and press Enter to kill the server (or anything else to ignore): " input  
      
    if \[ "$input" \== "k" \]; then  
        echo "🛑 Stopping and removing ublog..."  
        docker rm \-f ublog  
        echo "👋 All clean\! Server stopped."  
        break  
    else  
        echo "👍 Keeping the server running."  
    fi  
done  
```
2.2. run it
```bash 
chmod +x ./run.sh
```
```bash
./run.sh
```