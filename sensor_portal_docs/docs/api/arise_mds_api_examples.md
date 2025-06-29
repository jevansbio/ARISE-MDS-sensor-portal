# ARISE MDS API – Example Usage in R and Python

This document provides simple examples demonstrating how to interact with the ARISE MDS API using both R and Python.

---

## 1. Get an API Token

**Endpoint**: `POST /api-token-auth/`

**Python**
```python
import requests

url = "https://arisemdsvm.science.uva.nl/api-token-auth/"
data = {"username": "your_username", "password": "your_password"}
response = requests.post(url, data=data)
token = response.json().get("token")
print("Token:", token)
```

**R**
```r
library(httr)

url <- "https://arisemdsvm.science.uva.nl/api-token-auth/"
response <- POST(url, body = list(username = "your_username", password = "your_password"), encode = "form")
token <- content(response)$token
print(token)
```

---

## 2. Retrieve the First Page of Deployments

**Endpoint**: `GET /api/deployment/`

**Python**
```python
headers = {"Authorization": f"token {token}"}
response = requests.get("https://arisemdsvm.science.uva.nl/api/deployment/", headers=headers)
print(response.json())
```

**R**
```r
headers <- add_headers(Authorization = paste("token", token))
response <- GET("https://arisemdsvm.science.uva.nl/api/deployment/", headers)
print(content(response))
```

---

## 3. Handle Paginated Data (Deployments)

**Python**
```python
url = "https://arisemdsvm.science.uva.nl/api/deployment/"
all_results = []

while url:
    response = requests.get(url, headers=headers)
    data = response.json()
    all_results.extend(data["results"])
    url = data.get("next")

print(f"Total deployments: {len(all_results)}")
```

**R**
```r
url <- "https://arisemdsvm.science.uva.nl/api/deployment/"
all_results <- list()

while (!is.null(url)) {
  response <- GET(url, headers)
  data <- content(response)
  all_results <- c(all_results, data$results)
  url <- data$`next`
}

print(length(all_results))
```

---

## 4. Filter Observations by Deployment and Source

**Endpoint**: `GET /api/observation/`

**Python**
```python
# Filter by deployment
params = {"deployment": "deployment_id"}
response = requests.get("https://arisemdsvm.science.uva.nl/api/observation/", headers=headers, params=params)
print(response.json())

# Filter by source
params = {"source": "source_id_or_name"}
response = requests.get("https://arisemdsvm.science.uva.nl/api/observation/", headers=headers, params=params)
print(response.json())
```

**R**
```r
# Filter by deployment
response <- GET("https://arisemdsvm.science.uva.nl/api/observation/", headers, query = list(deployment = "deployment_id"))
print(content(response))

# Filter by source
response <- GET("https://arisemdsvm.science.uva.nl/api/observation/", headers, query = list(source = "source_id_or_name"))
print(content(response))
```