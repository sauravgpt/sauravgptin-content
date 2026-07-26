---
title: "Non-Functional Requirements"
order: 2
description: "Learn how to define, reason about, and design systems around critical non-functional requirements such as availability, latency, scale, and consistency."
---

In real-world systems, **functionality alone is not enough**. Two applications can share identical feature sets yet deliver vastly different experiences: one feels instant and reliable, while the other feels sluggish and prone to crashing.

These differences are defined by **Non-Functional Requirements (NFRs)**. If functional requirements define *what* a system does, NFRs define *how well* it does it. They are the constraints—availability, latency, consistency, and scale—that shape every architectural decision you will make.

---

## Concept Overview

System design is fundamentally an exercise in balancing competing forces. You cannot purely optimize for one NFR without making trade-offs in another. This module guides you through these critical dimensions:

### Availability & Reliability
The most fundamental requirement is that your system exists when users need it. We explore how to rigorously define "uptime" using **SLAs, SLOs, and SLIs**, moving beyond vague promises to measurable engineering targets. You will learn to distinguish **High Availability** (minimizing downtime) from **Fault Tolerance** (zero downtime), and how redundancy patterns like active-passive and active-active replication serve these goals.

### Performance & Scalability
A running system is useless if it is too slow to use or collapses under load. We dive into **Latency**, debunking the "myth of the average" to focus on P99 percentiles as the true measure of user satisfaction. As your user base grows, you must **Scale**. We examine the limits of vertical scaling (buying bigger hardware) versus the complexity of horizontal scaling (distributing load), and how analyzing your **Read-Write Ratio** dictates the optimal database and caching strategies.

### Data Integrity & Trade-offs
In a distributed environment, the laws of physics impose hard limits. We explore **Consistency** models—from strict linearizability to eventual consistency—and the specific trade-offs mandated by the **CAP Theorem**. Finally, we cover **Durability**, the guarantee that acknowledged writes are permanently preserved, ensuring that your system remains trustworthy even in the face of catastrophic infrastructure failure.

---

## Why Master Non-Functional Requirements?

NFRs are often the "silent killers" of system design. They are the first topic in senior engineering interviews and the primary cause of production outages.

By mastering these concepts, you move beyond simply coding features to engineering robust systems. You will be able to:

- **Ask the right questions** to uncover hidden constraints before writing a single line of code.
- **Justify architectural decisions** based on concrete data rather than intuition.
- **Navigate trade-offs** to select the right tool for the job, avoiding the traps of over-engineering or under-provisioning.

---

## What’s Next

You are now ready to explore the specific constraints that shape modern architectures.

Begin with **Availability** to understand the most foundational expectation of any distributed system.
