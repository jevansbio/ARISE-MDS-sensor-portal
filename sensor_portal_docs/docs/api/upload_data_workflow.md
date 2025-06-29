# Uploading a Data File to the ARISE MDS API

This document demonstrates how to authenticate with the ARISE MDS API and upload a data file using both **R** and **Python**. The ARISE MDS API expects authentication tokens to be prefixed with `token`, and supports a browsable schema at [https://arisemdsvm.science.uva.nl/api/schema/swagger-ui/](https://arisemdsvm.science.uva.nl/api/schema/swagger-ui/) as well as a raw OpenAPI schema at [https://arisemdsvm.science.uva.nl/api/schema/](https://arisemdsvm.science.uva.nl/api/schema/).

---

## Upload Example 1: JPEG Files

### R Example – Upload JPEG Files

```r
jpeg_files <- list(
  deployment = "deployment_id_here",
  files = upload_file("path/to/image1.jpeg"),
  files = upload_file("path/to/image2.jpeg")
)

upload_response <- POST(
  url = "https://arisemdsvm.science.uva.nl/api/datafile/",
  add_headers(Authorization = paste("token", token)),
  body = jpeg_files,
  encode = "multipart"
)
content(upload_response)
```

### Python Example – Upload JPEG Files

```python
upload_url = "https://arisemdsvm.science.uva.nl/api/datafile/"
headers = {"Authorization": f"token {token}"}

data = {"deployment": "deployment_id_here"}
files = [
    ("files", ("image1.jpeg", open("path/to/image1.jpeg", "rb"), "image/jpeg")),
    ("files", ("image2.jpeg", open("path/to/image2.jpeg", "rb"), "image/jpeg"))
]

response = requests.post(upload_url, headers=headers, files=files, data=data)
print(response.json())
```

## Upload Example 2: .dat Files with `recording_dt`

### R Example – Upload Multiple .dat Files with `recording_dt`

```r
dat_upload <- list(
  deployment = "deployment_id_here",
  recording_dt = c("2024-10-21T14:30:00Z", "2024-10-21T14:35:00Z"),
  files = upload_file("path/to/datafile1.dat"),
  files = upload_file("path/to/datafile2.dat")
)

response <- POST(
  url = "https://arisemdsvm.science.uva.nl/api/datafile/",
  add_headers(Authorization = paste("token", token)),
  body = dat_upload,
  encode = "multipart"
)
content(response)
```

### Python Example – Upload Multiple .dat Files with `recording_dt`

```python
data = {
    "deployment": "deployment_id_here",
    "recording_dt": [
        "2024-10-21T14:30:00Z",
        "2024-10-21T14:35:00Z"
    ]
}
files = [
    ("files", ("datafile1.dat", open("path/to/datafile1.dat", "rb"), "application/octet-stream")),
    ("files", ("datafile2.dat", open("path/to/datafile2.dat", "rb"), "application/octet-stream"))
]

response = requests.post(upload_url, headers=headers, files=files, data=data)
print(response.json())
```

---

## Upload Example 3: Multipart Chunked Upload

### Python Example – Basic Multipart Upload

```python
import requests, os, hashlib, json
from io import BytesIO

upload_url = "https://arisemdsvm.science.uva.nl/api/datafile/"
headers = {"Authorization": f"token {token}"}

filename = "path/to/bigfile.dat"
chunk_size = 100 * 1024 * 1024  # 100MB
file_size = os.path.getsize(filename)
md5 = hashlib.md5()

with open(filename, "rb") as f:
    offset = 0
    while chunk := f.read(chunk_size):
        md5.update(chunk)
        content_range = f"bytes {offset}-{offset + len(chunk) - 1}/{file_size}"
        headers["Content-Range"] = content_range

        data = {
            "deployment": "deployment_id_here",
            "recording_dt": ["2024-10-21T14:30:00Z"]
        }
        if offset + len(chunk) == file_size:
            data["extra_data"] = json.dumps({"md5_checksum": md5.hexdigest()})

        files = [("files", ("bigfile.dat", BytesIO(chunk), "application/octet-stream"))]
        response = requests.post(upload_url, headers=headers, files=files, data=data)
        print(f"Chunk {offset // chunk_size + 1} response:", response.status_code)

        offset += len(chunk)
```

If a chunk upload fails or returns an error status code, the client can retry the same chunk using the same `Content-Range` header. Below is a recommended pattern for checking and retrying.

### Python Example with Retry Logic

```python
import requests, os, hashlib, json
from io import BytesIO

upload_url = "https://arisemdsvm.science.uva.nl/api/datafile/"
headers = {"Authorization": f"token {token}"}

filename = "path/to/bigfile.dat"
chunk_size = 100 * 1024 * 1024  # 100MB
file_size = os.path.getsize(filename)
md5 = hashlib.md5()

with open(filename, "rb") as f:
    offset = 0
    part = 1
    while chunk := f.read(chunk_size):
        md5.update(chunk)
        content_range = f"bytes {offset}-{offset + len(chunk) - 1}/{file_size}"
        headers["Content-Range"] = content_range

        data = {
            "deployment": "deployment_id_here",
            "recording_dt": ["2024-10-21T14:30:00Z"]
        }
        if offset + len(chunk) == file_size:
            data["extra_data"] = json.dumps({"md5_checksum": md5.hexdigest()})

        files = [
            ("files", ("bigfile.dat", BytesIO(chunk), "application/octet-stream"))
        ]

        retries = 3
        while retries > 0:
            response = requests.post(upload_url, headers=headers, files=files, data=data)
            if response.status_code == 200:
                print(f"Chunk {part} uploaded successfully.")
                break
            else:
                print(f"Chunk {part} failed with status {response.status_code}, retrying...")
                retries -= 1

        if retries == 0:
            print(f"Chunk {part} failed after multiple retries.")
            break

        offset += len(chunk)
        part += 1
```

---

### R Example – Basic Multipart Upload

```r
library(httr)
library(digest)

upload_url <- "https://arisemdsvm.science.uva.nl/api/datafile/"
file_path <- "path/to/bigfile.dat"
file_size <- file.info(file_path)$size
chunk_size <- 100 * 1024 * 1024  # 100MB
con <- file(file_path, "rb")
offset <- 0
md5_hash <- md5(file_path, algo = "md5", file = TRUE)

repeat {
  chunk <- readBin(con, "raw", n = chunk_size)
  if (length(chunk) == 0) break

  end_byte <- offset + length(chunk) - 1
  content_range <- paste0("bytes ", offset, "-", end_byte, "/", file_size)

  headers <- add_headers(
    Authorization = paste("token", token),
    `Content-Range` = content_range
  )

  data <- list(
    deployment = "deployment_id_here",
    recording_dt = "2024-10-21T14:30:00Z"
  )

  if (end_byte + 1 == file_size) {
    data$extra_data <- paste0('{"md5_checksum": "', md5_hash, '"}')
  }

  files <- list(files = upload_file(file_path, type = "application/octet-stream"))

  response <- POST(upload_url, headers, body = c(data, files), encode = "multipart")
  print(paste("Chunk", offset %/% chunk_size + 1, "response:", status_code(response)))

  offset <- offset + length(chunk)
}

close(con)
```

### R Example with Retry Logic

```r
library(httr)
library(digest)

upload_url <- "https://arisemdsvm.science.uva.nl/api/datafile/"
file_path <- "path/to/bigfile.dat"
file_size <- file.info(file_path)$size
chunk_size <- 100 * 1024 * 1024  # 100MB
con <- file(file_path, "rb")
offset <- 0
part <- 1
md5_hash <- md5(file_path, algo = "md5", file = TRUE)

repeat {
  chunk <- readBin(con, "raw", n = chunk_size)
  if (length(chunk) == 0) break

  end_byte <- offset + length(chunk) - 1
  content_range <- paste0("bytes ", offset, "-", end_byte, "/", file_size)

  headers <- add_headers(
    Authorization = paste("token", token),
    `Content-Range` = content_range
  )

  data <- list(
    deployment = "deployment_id_here",
    recording_dt = "2024-10-21T14:30:00Z"
  )

  if (end_byte + 1 == file_size) {
    data$extra_data <- paste0('{"md5_checksum": "', md5_hash, '"}')
  }

  files <- list(files = upload_file(file_path, type = "application/octet-stream"))

  retries <- 3
  repeat {
    response <- POST(upload_url, headers, body = c(data, files), encode = "multipart")
    if (status_code(response) == 200 || retries == 0) break
    message(paste("Chunk", part, "failed. Retrying..."))
    retries <- retries - 1
  }

  if (retries == 0) {
    message(paste("Chunk", part, "failed after multiple attempts."))
    break
  }

  print(paste("Chunk", part, "uploaded successfully."))
  offset <- offset + length(chunk)
  part <- part + 1
}

close(con)
```

---

## Notes

- Use `Content-Range` to indicate chunk position.
- The final chunk must include a valid `md5_checksum`.
- If a chunk fails to upload (non-200 response), retry the same chunk.
- You can use the response payload (if any) to confirm status or progress.



