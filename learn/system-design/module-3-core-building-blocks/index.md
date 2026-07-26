---
title: "Core Building Blocks"
order: 3
description: "Learn the essential components and patterns used to build scalable, resilient, and high-performance distributed systems."
---

## Module 3: Core Building Blocks

Once you understand system fundamentals and non-functional requirements, the next step is learning the **core building blocks** used to construct real-world systems.

This module introduces the most commonly used **infrastructure components, architectural patterns, and design techniques** that enable systems to scale, remain available under load, and behave predictably under failure.

These building blocks appear repeatedly in production systems and system design interviews.

---

## What You Will Learn

### Load Balancing (Introduction & Techniques)
Learn how traffic is distributed across multiple servers.  
Understand why load balancing is essential for scalability and availability, and explore common algorithms such as round-robin, least connections, and hashing-based routing.

---

### Content Delivery Networks (CDN)
Understand how content is served closer to users.  
Learn how CDNs reduce latency, offload origin servers, and improve global performance.

---

### Advanced Caching
Go beyond basic caching concepts.  
Learn advanced cache placement strategies, eviction policies, and consistency trade-offs in distributed systems.

---

### Rate Limiting
Learn how systems protect themselves from abuse and overload.  
Understand common rate-limiting algorithms and how they help maintain system stability and fairness.

---

### Forward Proxy & Reverse Proxy
Understand how proxies sit in the request path.  
Learn the differences between forward and reverse proxies and their roles in security, performance, and traffic control.

---

### Scale Cube
Learn a structured approach to scaling systems.  
Understand how systems scale along different dimensions—functional decomposition, data partitioning, and replication.

---

### Idempotency
Understand how systems safely handle retries.  
Learn why idempotency is critical for distributed systems, especially in the presence of network failures and duplicate requests.

---

### Bloom Filters
Learn how probabilistic data structures improve efficiency.  
Understand how Bloom filters enable fast membership checks while trading off accuracy for performance and memory efficiency.

---

### Pub/Sub & Event-Driven Architectures
Understand asynchronous communication patterns.  
Learn how publish–subscribe systems decouple producers and consumers and enable scalable, event-driven designs.

---

### Monolith vs Microservices
Learn how systems are structured at a macro level.  
Understand the trade-offs between monolithic and microservices architectures, and why there is no one-size-fits-all solution.

---

## Why This Module Matters

These building blocks are the **tools of the trade** for system designers.

Mastering them allows you to:

- Translate non-functional requirements into concrete architecture
- Choose the right component for the right problem
- Avoid common scalability and reliability pitfalls
- Design systems that evolve gracefully as requirements grow

---

## Outcome of This Module

By the end of this module, you will be able to:

- Recognize common system design patterns in real systems
- Explain why specific components are used in an architecture
- Reason about trade-offs between complexity, performance, and reliability
- Confidently apply these building blocks in system design discussions

---

## What’s Next

With these core building blocks in place, you will be ready to design **end-to-end systems**, where multiple components work together to meet strict non-functional requirements.

Begin with **Load Balancing** to understand how scalable systems handle traffic from day one.
