---
title: 'Failover & Health Monitoring: The Heartbeat Pattern'
secondaryTitle: 'Heartbeat Pattern'
order: 11
description: 'Master the Heartbeat pattern for failure detection in distributed systems. Learn about push vs pull models, failure thresholds, and preventing false positives in high-scale architectures.'
---

## Concept Overview

In a distributed system, components fail. Servers crash, networks partition, and processes hang. The fundamental challenge is: **How does System A know that System B is still functioning?**

You cannot simply "know" remote state. You must actively monitor it. The **Heartbeat** pattern is the standard mechanism that provides this visibility by having components periodically signal their existence to a monitoring service or peer.

```callout
{
  "type": "info",
  "title": "Heartbeat vs. Health Check",
  "content": "While often used interchangeably, there is a nuance:\n- **Heartbeat**: A simple signal (\"I am alive\"). Low overhead, high frequency.\n- **Health Check**: A richer status report (\"I am alive, CPU is 40%, DB connection is active\"). Higher overhead, typically lower frequency."
}
```

## The Role of Heartbeats

Heartbeats serve two critical functions in reliability engineering:

1.  **Failure Detection**: Identifying when a node has died or become unreachable so the system can trigger recovery (e.g., spinning up a replacement).
2.  **Route Management**: Ensuring traffic is only sent to healthy instances (e.g., removing a failed node from a load balancer pool).

```lottie
{ "src": "https://cdn.jsdelivr.net/gh/sauravgpt/sauravgptin-content@main/assets/lottie/system-design/heartbeat-healthy-state.lottie", "loop": true, "autoplay": true, "speed": 1 }
```

## Real-World Use Cases

### 1. Load Balancers (AWS ELB, NGINX)
Load balancers must track which backend servers are eligible to receive traffic.
*   **Mechanism**: The Load Balancer sends a ping (or expects a push) every few seconds.
*   **Failure**: If a backend misses `N` consecutive heartbeats, it is marked "Unhealthy" and drained of connections.
*   **Recovery**: When heartbeats resume for `M` intervals, it is marked "Healthy" and reintroduced to the pool.

### 2. Leader Election (ZooKeeper, Etcd, Raft)
In consensus algorithms like Raft, the elected Leader maintains authority by asserting its presence.
*   **Mechanism**: The Leader broadcasts periodic heartbeats to all Followers.
*   **Failure**: If Followers stop receiving heartbeats for a `randomized election timeout`, they assume the Leader is dead and trigger a new election.

### 3. Service Registries (Netflix Eureka)
Microservices register themselves with a central registry to be discoverable.
*   **Mechanism**: Services send a heartbeat (e.g., every 30s) to "renew" their lease.
*   **Failure**: If the registry doesn't receive a heartbeat within the expiration window (e.g., 90s), it expunges the service instance from the directory.

---

```quiz
{
  "question": "Which of the following describes a 'False Positive' in the context of heartbeats?",
  "options": [
    "A server is dead, and the monitor correctly marks it as dead.",
    "A server is alive, but the monitor incorrectly marks it as dead.",
    "A server is dead, but the monitor thinks it is alive.",
    "A server sends a heartbeat faster than the configured interval."
  ],
  "correctAnswerIndex": 1,
  "explanation": "A false positive occurs when the monitoring system incorrectly believes a healthy node has failed, often due to network congestion or long Garbage Collection (GC) pauses."
}
```

---

## Design Strategies: Push vs. Pull

There are two primary ways to implement heartbeats.

### 1. Push Model (Active Reporting)
The monitored service actively sends signals to the monitor.

*   **Pros**: Failures are detected immediately when the stream stops. Ideal for ephemeral instances.
*   **Cons**: Global synchronization can cause **Thundering Herd** problems if all servers send heartbeats simultaneously.
*   **Use Case**: IoT devices reporting to a central hub.

### 2. Pull Model (Polling)
The monitor actively sends requests ("Are you there?") to the services.

*   **Pros**: The monitor controls the load. It won't get overwhelmed by a flood of incoming heartbeats.
*   **Cons**: Detection latency is higher (Monitor Request + Network RTT + Service Processing + Monitor Timeout).
*   **Use Case**: AWS Route53 Health Checks, Prometheus scraping metrics.

```match
{
  "question": "Match the scenario to the optimal Strategy",
  "pairs": [
    {
      "left": "IoT Sensors (1M+ devices)",
      "right": "Push (to avoid monitor bottleneck)"
    },
    {
      "left": "Prometheus Monitoring",
      "right": "Pull (Scraping endpoint)"
    },
    {
      "left": "Load Balancer behind Firewall",
      "right": "Pull (Monitor controls access)"
    }
  ]
}
```

## Implementation Considerations

### 1. Frequency & Timeouts
There is a fundamental tradeoff between **Detection Speed** and **System Overhead**.

*   **Aggressive (e.g., 1s interval)**: fast failover, but high risk of **False Positives** due to network blips or GC pauses.
*   **Conservative (e.g., 30s interval)**: stable, but users may experience errors for 30s before failover occurs.

**Rule of Thumb**: Set the **Timeout** to `3x` the **Interval**.
*   *Heartbeat Interval*: 5 seconds
*   *Failure Timeout*: 15 seconds (3 missed beats)

### 2. The "Flapping" Problem
A service that is on the edge of failure (e.g., overloaded CPU) might succeed one heartbeat and fail the next. This causes it to be added and removed from the pool repeatedly ("flapping").
*   **Solution**: Use **Hysteresis**. Require `N` successful heartbeats to join, but `M` failed heartbeats to leave. Usually `N > M` to prioritize stability.

### 3. Zombie Processes
A process might be effectively dead (deadlocked threads) but still responding to heartbeats on a separate I/O thread.
*   **Solution**: Deep Health Checks. Ensure the heartbeat logic validates internal dependencies (DB connection, thread pool availability) rather than just returning `200 OK`.

```quiz
{
  "question": "You have a system where 99.99% availability is critical. What is the biggest risk of setting a very low heartbeat interval (e.g., 100ms)?",
  "options": [
    "The servers will run out of disk space.",
    "The monitor will receive too much data and crash.",
    "Network jitter will cause frequent 'false positive' failovers.",
    "The database will become inconsistent."
  ],
  "correctAnswerIndex": 2,
  "explanation": "Extremely aggressive intervals make the system sensitive to minor network variances (jitter), executing expensive failover procedures for healthy nodes."
}
```

## Summary & Key Takeaways

*   **Heartbeats are the pulse of a distributed system:** They bridge the gap between "knowing" and "guessing" system state.
*   **Tradeoffs are key:** Faster is not always better. Aggressive heartbeats lead to instability; slow heartbeats lead to user-facing downtime.
*   **Context matters:** A simple ping is enough for a load balancer, but a leader lease needs strict timing guarantees.
*   **Design for failure:** Assume heartbeats will be missed due to network issues, not just server crashes. Use thresholds (e.g., 3 misses) to smooth out noise.
