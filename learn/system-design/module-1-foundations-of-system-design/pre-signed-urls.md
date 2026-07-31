---
title: 'Direct-to-Object-Storage: Pre-signed URLs'
secondaryTitle: 'Pre-signed URLs'
order: 10
description: 'Learn how to scale file uploads and downloads by decoupling data transfer from application logic using Pre-signed URLs.'
---

## Concept Overview

In traditional web architectures, file uploads typically flow through the application server before reaching permanent storage. While straightforward for small files, this pattern becomes a critical bottleneck at scale.

**Pre-signed URLs** offer a powerful alternative by decoupling the **Control Plane** (authentication, authorization) from the **Data Plane** (high-volume data transfer), allowing clients to interact directly with object storage providers like AWS S3, Google Cloud Storage, or Azure Blob Storage securely.

## The Bottleneck of Traditional Uploads

When a user uploads a large file (e.g., a 4K video) through your application server:
1.  **Double Bandwidth Cost**: Ingress to your server + Egress to the storage bucket.
2.  **Resource Contention**: The server's CPU and memory are tied up streaming bytes instead of handling business logic.
3.  **Connection Limits**: Long-lived connections exhaust thread pools or file descriptors, limiting the number of concurrent users.

```lottie
{ "src": "https://cdn.jsdelivr.net/gh/sauravgpt/sauravgptin-content@main/assets/lottie/system-design/pre-signed-urls-traditional-upload.lottie", "loop": true, "autoplay": true, "speed": 1 }
```

## How Pre-signed URLs Work

A Pre-signed URL is a time-limited, cryptographically signed link that grants specific permissions (e.g., `PUT` an object) to a specific resource.

### The Workflow

1.  **Request**: Client requests permission to upload a file.
2.  **Generate**: Application verifies identity/permissions and requests a signed URL from the Storage Provider using its own credentials.
3.  **Return**: Application returns the signed URL to the client.
4.  **Transfer**: Client uploads the file directly to the Storage Provider using the signed URL.

```lottie
{ "src": "https://cdn.jsdelivr.net/gh/sauravgpt/sauravgptin-content@main/assets/lottie/system-design/pre-signed-urls-signed-url-flow.lottie", "loop": true, "autoplay": true, "speed": 0.7 }
```

```callout
{
  "type": "info",
  "title": "Security Mechanism",
  "content": "The URL contains a query string with a <strong>signature</strong> generated using the server's private keys. If a user tries to tamper with the URL (e.g., changing the file path or extending the expiration), the signature validation fails at the Storage Provider level."
}
```

## Real-World Use Cases

### 1. User-Generated Content (UGC) Platforms
Platforms hosting massive media libraries avoid routing Terabytes of video data through their backend.
*   **Scenario**: A creator uploading a raw video file.
*   **Benefit**: Bandwidth intensive uploads are offloaded completely. Backend scales based on *requests per second* (generating tiny URL strings), not *gigabytes per second*.

### 2. Secure Artifact Delivery
Delivering build logs or binaries in a CI/CD pipeline purely on demand.
*   **Scenario**: A developer requests a build log from a private S3 bucket.
*   **Benefit**: Authorization is checked once by the API, and a temporary link (valid for 5 mins) is essentially "handed over" to the developer for direct download.

### 3. Temporary Data Sharing (P2P-ish)
Allowing two users to share files without making the file "public".
*   **Scenario**: Sending a legal document attachment in a secure chat app.
*   **Benefit**: The file remains private (ACL=Private). Access is granted strictly on a per-request basis via the generated URL.

## Read vs. Write Patterns

Pre-signed URLs are not just for uploads. They are equally critical for controlled downloads.

### Write Strategy (PUT)
Used for uploads. Crucially, the **Content-Type** and headers signed in the URL *must* match what the client eventually sends.
*   **Mechanism**: Signed `PUT` request.
*   **Constraint**: The signature often locks in the exact file size or checksum to prevent "swapping" attacks.

### Read Strategy (GET)
Used to serve private content.
*   **Mechanism**: Signed `GET` request.
*   **CDN Integration**: Pre-signed cookies or URLs can often be used with CDNs (like CloudFront) to serve private content at the edge, rather than hitting the origin bucket directly.

```quiz
{
  "question": "Which of the following modifications to a pre-signed URL by a client will cause the request to fail?",
  "options": [
    "Uploading the file before the expiration time",
    "Changing the target file path in the query parameters",
    "Using the exact HTTP method specified in the signature",
    "Adding a standard User-Agent header"
  ],
  "correctAnswerIndex": 1,
  "explanation": "The cryptographic signature includes the resource path. Any alteration to the path, query parameters, or expiration time invalidates the signature, causing the storage provider to reject the request."
}
```

## Failure & Scale Considerations

### 1. The "Ghost Upload" Problem
A user might request a URL but never perform the upload, or the upload might fail halfway.
*   **Impact**: Your database might have a record of "File Pending" that never completes.
*   **Solution**: Use **Event Notifications** (e.g., S3 Event Notifications to SQS/Lambda) to trigger a "Success" callback only when the file actually lands in the bucket. Don't trust the client's "I'm done" message blindly.

### 2. Expiration Management
Balancing usability vs. security.
*   **Too Short**: Uploads fail on slow connections (especially mobile).
*   **Too Long**: Increased risk window if the URL is leaked.
*   **Best Practice**: Use shorter expirations for downloads (e.g., 5 mins) and reasonably longer ones for uploads (e.g., 30-60 mins), potentially combined with **Multipart Uploads** for very large files (where each chunk gets its own signed URL).

### 3. Client Capability
Not all clients can easily make direct `PUT` requests to 3rd party domains due to **CORS (Cross-Origin Resource Sharing)**.
*   **Requirement**: You must configure CORS on the storage bucket to allow `PUT/POST` requests from your application's domain.

1. **Configure CORS**
   Update Object Storage Bucket policy to allow `Original: https://your-app.com` and `Method: PUT`.
2. **Generate URL**
   Backend calls S3 `getSignedUrl` operation.
3. **Handle Client Upload**
   Client uses `fetch(signedUrl, { method: 'PUT', body: file })`.

## Comparison: Pre-signed vs. Proxying

| Feature | Pre-signed URLs | Proxying via Server |
| :--- | :--- | :--- |
| **Scalability** | Extremely High (Offloaded) | Low (Bound by Server I/O) |
| **Complexity** | Medium (CORS, Async flow) | Low (Client just talks to API) |
| **Security** | High (Granular, Time-bound) | High (Server controls stream) |
| **Cost** | Low (Pay only Storage Transfer) | High (Pay App Ingress + Egress) |
| **Latency** | Best (Direct to nearest region) | Higher (Extra hop) |

```quiz
{
  "question": "Why is configuring CORS necessary when using Pre-signed URLs for uploads?",
  "options": [
    "To encrypt the data transfer",
    "To allow the browser to make a request to a different domain (the storage provider) than the one serving the app",
    "To prevent the Pre-signed URL from expiring",
    "To compress the file during upload"
  ],
  "correctAnswerIndex": 1,
  "explanation": "Browsers enforce the Same-Origin Policy. Since the web app domain (e.g., myapp.com) differs from the storage endpoint (e.g., s3.amazonaws.com), the storage bucket must explicitly allow cross-origin requests via CORS headers."
}
```

## Summary

Pre-signed URLs are the industry standard for handling file transfers in distributed systems. By treating the application server purely as a **control plane**—issuing permits rather than moving boxes—you achieve better performance, lower costs, and infinite scalability for your file I/O operations.
