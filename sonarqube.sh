#!/bin/sh

# 1. Start the SonarQube container
docker run -d --name sonarqube --restart always \
           --network runner-net -p 9000:9000 \
           -e SONAR_ES_BOOTSTRAP_CHECKS_DISABLE=true \
           sonarqube:26.10.0.133078-community

# 2. Wait until SonarQube is fully up and running
echo "Waiting for SonarQube to initialize..."
until curl -s http://localhost:9000/api/system/status | grep -q '"status":"UP"'; do
  sleep 5
done
echo "SonarQube is UP."

# 3. Change the default admin password (admin/admin -> new password)
NEW_PASSWORD="YourSecurePassword123!"
curl -s -u admin:admin -X POST "http://localhost:9000/api/users/change_password" \
  --data-urlencode "login=admin" \
  --data-urlencode "previousPassword=admin" \
  --data-urlencode "password=$NEW_PASSWORD" > /dev/null
echo "Admin password updated."

# 4. Generate a persistent API token for your CI/CD pipeline
TOKEN_RESPONSE=$(curl -s -u admin:$NEW_PASSWORD -X POST "http://localhost:9000/api/user_tokens/generate" \
  --data-urlencode "name=cicd-pipeline-token")

# Extract the token string (requires jq or basic grep/sed)
CICD_TOKEN=$(echo "$TOKEN_RESPONSE" | grep -o '"token":"[^"]*' | cut -d'"' -f4)

echo "----------------------------------------"
echo "Your CI/CD Token: $CICD_TOKEN"
echo "----------------------------------------"