# Device Registration API Documentation

## Base URL
```
http://localhost:8080/api
```

## Endpoints

### 1. Get All Devices
**GET** `/api/devices`

Returns a list of all registered devices.

**Response:**
```json
{
  "status": "success",
  "count": 5,
  "devices": [
    {
      "id": 1,
      "name": "My iPhone",
      "os": "iOS",
      "browser": "Safari",
      "ip": "192.168.1.1",
      "registered_at": "2025-01-06 10:30:00"
    }
  ]
}
```

**Example:**
```bash
curl http://localhost:8080/api/devices
```

---

### 2. Get Device by ID
**GET** `/api/devices/<device_id>`

Returns a specific device by its ID.

**Parameters:**
- `device_id` (path, required): Device ID

**Response (Success):**
```json
{
  "status": "success",
  "device": {
    "id": 1,
    "name": "My iPhone",
    "os": "iOS",
    "browser": "Safari",
    "ip": "192.168.1.1",
    "registered_at": "2025-01-06 10:30:00"
  }
}
```

**Response (Not Found):**
```json
{
  "status": "error",
  "message": "Device not found"
}
```

**Example:**
```bash
curl http://localhost:8080/api/devices/1
```

---

### 3. Check Device by Name
**GET** `/api/devices/check?name=<device_name>`

Checks if a device exists by name.

**Parameters:**
- `name` (query, required): Device name to check

**Response (Device Exists):**
```json
{
  "status": "success",
  "exists": true,
  "device": {
    "id": 1,
    "name": "My iPhone",
    "os": "iOS",
    "browser": "Safari",
    "ip": "192.168.1.1",
    "registered_at": "2025-01-06 10:30:00"
  }
}
```

**Response (Device Not Found):**
```json
{
  "status": "success",
  "exists": false,
  "message": "Device not found"
}
```

**Example:**
```bash
curl "http://localhost:8080/api/devices/check?name=My%20iPhone"
```

---

### 4. Search Devices
**GET** `/api/devices/search?q=<query>`

Searches devices by name, OS, or browser.

**Parameters:**
- `q` (query, required): Search query

**Response:**
```json
{
  "status": "success",
  "query": "iPhone",
  "count": 2,
  "devices": [
    {
      "id": 1,
      "name": "My iPhone",
      "os": "iOS",
      "browser": "Safari",
      "ip": "192.168.1.1",
      "registered_at": "2025-01-06 10:30:00"
    }
  ]
}
```

**Example:**
```bash
curl "http://localhost:8080/api/devices/search?q=iPhone"
curl "http://localhost:8080/api/devices/search?q=Chrome"
curl "http://localhost:8080/api/devices/search?q=Windows"
```

---

### 5. Get Device Statistics
**GET** `/api/devices/stats`

Returns device statistics including counts by OS, browser, and recent registrations.

**Response:**
```json
{
  "status": "success",
  "stats": {
    "total": 10,
    "recent_24h": 3,
    "recent_7d": 8,
    "by_os": {
      "iOS": 4,
      "Windows": 3,
      "macOS": 2,
      "Android": 1
    },
    "by_browser": {
      "Chrome": 5,
      "Safari": 3,
      "Firefox": 2
    }
  }
}
```

**Example:**
```bash
curl http://localhost:8080/api/devices/stats
```

---

## Error Responses

All endpoints may return errors in the following format:

```json
{
  "status": "error",
  "message": "Error description"
}
```

**HTTP Status Codes:**
- `200` - Success
- `400` - Bad Request (missing required parameters)
- `404` - Not Found (device not found)
- `500` - Internal Server Error

---

## Usage Examples

### JavaScript/Fetch
```javascript
// Get all devices
fetch('http://localhost:8080/api/devices')
  .then(res => res.json())
  .then(data => console.log(data));

// Check if device exists
fetch('http://localhost:8080/api/devices/check?name=My%20Device')
  .then(res => res.json())
  .then(data => {
    if (data.exists) {
      console.log('Device found:', data.device);
    } else {
      console.log('Device not found');
    }
  });

// Search devices
fetch('http://localhost:8080/api/devices/search?q=iPhone')
  .then(res => res.json())
  .then(data => console.log(data.devices));

// Get statistics
fetch('http://localhost:8080/api/devices/stats')
  .then(res => res.json())
  .then(data => console.log(data.stats));
```

### Python/Requests
```python
import requests

# Get all devices
response = requests.get('http://localhost:8080/api/devices')
devices = response.json()

# Check device
response = requests.get('http://localhost:8080/api/devices/check', 
                       params={'name': 'My Device'})
result = response.json()

# Search devices
response = requests.get('http://localhost:8080/api/devices/search', 
                       params={'q': 'iPhone'})
results = response.json()

# Get statistics
response = requests.get('http://localhost:8080/api/devices/stats')
stats = response.json()
```

---

## Notes

- All endpoints return JSON responses
- Device IDs are auto-incremented integers
- Search is case-insensitive and uses LIKE pattern matching
- Statistics are calculated in real-time
- All timestamps are in SQLite datetime format

