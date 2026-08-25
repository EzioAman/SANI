# SANI — Smart Armored Nexus Integration

### Edge AI Safety & Intelligence System

SANI (Smart Armored Nexus Integration) is an **Edge AI safety and intelligence system** designed to provide context-aware responses, environmental awareness, and decision support in connectivity-denied environments.

The system was designed around **Raspberry Pi and Qwen 1.5B**, with a focus on offline AI inference, GPS-independent navigation, dynamic digital floor-plan mapping, real-time environmental awareness, and scenario-based responses.

> **Bringing intelligent decision support to the edge — without depending on cloud connectivity.**

---

## 📜 Published Patent

SANI resulted in a published patent application:

### **System and Method for Autonomous Threat Detection in an Environment**

**Application No.: 202511133131**
**Published:** 2025
**Authority:** Intellectual Property India

The patent covers aspects of:

* Offline AI inference
* Adaptive threat detection
* Autonomous decision-support systems
* Edge AI deployment on low-power embedded devices such as the Raspberry Pi

The patent represents the intellectual-property outcome of the SANI project.

---

> [!IMPORTANT]
>
> ## Repository Notice
>
> **This repository does NOT contain the original working SANI implementation.**
>
> The original SANI codebase is no longer available in its complete form. This repository is preserved as a **project archive documenting the original concept, architecture, research, and development**.
>
> If you are looking for surviving code from the original SANI project, parts of the earlier implementation are available in **[Saumya Suman's SANI repository](https://github.com/saumyaaa78/SANI/tree/main/Code)**.
>
> **Do not clone or pull this repository expecting the original SANI system to run.** The contents here should not be considered a replacement for the original implementation.

---

## Overview

SANI was developed to explore how intelligent AI systems could operate directly on low-power edge hardware without depending on continuous internet connectivity or remote cloud infrastructure.

The system combined AI inference with environmental and contextual information to generate responses based on the surrounding situation.

The project explored:

* Edge AI inference
* Offline AI operation
* Context-aware responses
* Real-time environmental awareness
* GPS-independent navigation
* Dynamic digital floor-plan mapping
* Scenario-based response mechanisms
* Voice-based assistance
* Memory retention
* Autonomous decision support

---

## Core Architecture

```text
                         ┌───────────────────┐
                         │       USER        │
                         │   Voice / Input   │
                         └─────────┬─────────┘
                                   │
                                   ▼
                         ┌───────────────────┐
                         │    SANI SYSTEM    │
                         │                   │
                         │ AI + Context +    │
                         │ Decision Support  │
                         └─────────┬─────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
              ▼                    ▼                    ▼
       ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
       │ Environment │      │   Memory    │      │   Digital   │
       │  Awareness  │      │  Retention  │      │  Floor Plan │
       └──────┬──────┘      └──────┬──────┘      └──────┬──────┘
              │                    │                    │
              └────────────────────┼────────────────────┘
                                   │
                                   ▼
                         ┌───────────────────┐
                         │    Qwen 1.5B      │
                         │   Local AI Model  │
                         └─────────┬─────────┘
                                   │
                                   ▼
                         ┌───────────────────┐
                         │ Context-Aware     │
                         │ Response /        │
                         │ Decision Support  │
                         └───────────────────┘
```

---

## Key Features

### 🧠 Offline Edge AI

SANI was architected for **100% offline operation**, using Qwen 1.5B on Raspberry Pi for local AI inference.

This reduced dependence on cloud infrastructure and allowed the system to operate in connectivity-denied environments.

### 🗺️ GPS-Independent Navigation

SANI explored a navigation architecture that did not depend exclusively on GPS.

The system used environmental information and a **dynamic digital floor-plan representation** to maintain situational awareness.

### 👁️ Real-Time Environmental Awareness

The system incorporated environmental information to help interpret the surrounding situation.

This information could then be used as contextual input for AI-assisted responses and decision support.

### 🧩 Scenario-Based Responses

SANI was designed to respond according to the current scenario rather than treating every interaction identically.

Environmental information and contextual conditions could influence the system's resulting response.

### 🎙️ Voice-Based Assistance

Voice interaction provided a natural interface between the user and SANI.

```text
Voice Input
     ↓
Speech Recognition
     ↓
Context Processing
     ↓
AI Inference
     ↓
Decision Support
     ↓
Voice Response
```

### 💾 Memory Retention

SANI incorporated memory concepts to retain relevant information across interactions.

This allowed the system to maintain contextual information rather than treating every interaction as completely independent.

### ⚡ Autonomous Decision Support

The project explored AI-assisted decision support by combining AI inference with environmental and contextual information.

The objective was to assist the user in making decisions rather than provide unrestricted autonomous control.

---

## Technology Stack

| Component               | Technology                 |
| ----------------------- | -------------------------- |
| Edge Hardware           | Raspberry Pi               |
| AI Model                | Qwen 1.5B                  |
| Programming             | Python                     |
| AI Processing           | Local / Offline            |
| Environmental Awareness | Computer Vision            |
| Interaction             | Voice                      |
| Navigation              | GPS-independent            |
| Mapping                 | Dynamic Digital Floor Plan |

---

## Why Edge AI?

SANI was built around a simple question:

> **Can useful AI operate directly at the edge when connectivity is unavailable?**

A conventional cloud-dependent architecture can look like:

```text
Environment
     ↓
Internet
     ↓
Cloud Server
     ↓
Remote AI Inference
     ↓
Response
```

SANI explored an alternative:

```text
Environment
     ↓
Local Processing
     ↓
Local AI Inference
     ↓
Context + Memory
     ↓
Decision Support
```

This approach was intended to reduce dependency on external infrastructure while enabling AI capabilities on low-power embedded hardware.

---

## Engineering Focus

SANI brought together several areas of applied engineering:

* Edge AI
* Embedded Systems
* Small Language Models
* Offline AI Inference
* Computer Vision
* Voice Interfaces
* Context-Aware AI
* Spatial Mapping
* Autonomous Decision Support
* Human-AI Interaction

The central engineering challenge was exploring how meaningful AI capabilities could be deployed on **resource-constrained edge hardware**.

---

## Original Implementation

The original complete SANI codebase is no longer available.

However, parts of the original implementation have been preserved in **[Saumya Suman's SANI repository](https://github.com/saumyaaa78/SANI)**.

The surviving `Code` directory contains earlier components including:

```text
Code/
├── command_handler.py
├── config.py
├── memory_handler.py
├── sani_ai.py
├── sani_ai_phase1.py
├── sani_ai_Phase2.py
├── sheets_api.py
└── voice_input.py
```

For anyone interested in examining the surviving implementation:

**[View Original Code Archive →](https://github.com/saumyaaa78/SANI/tree/main/Code)**

> The surviving code should be considered an **archived portion of the original implementation**, not a complete representation of the final SANI system.

---

## Project Timeline

**February 2024 – April 2026**

SANI evolved as an engineering project exploring the deployment of intelligent systems on resource-constrained edge hardware.

The project progressed through experimentation with AI inference, environmental awareness, navigation, contextual responses, memory, and decision support.

---

## Project Status

**Archived / Not Currently Maintained**

The original working implementation is no longer available in its complete form.

This repository is preserved as a record of:

* The original SANI concept
* System architecture
* Engineering direction
* Research areas
* Project development
* Patent outcome

The concepts explored in SANI may be revisited in the future using newer edge hardware, AI models, and embedded technologies.

---

## Disclaimer

SANI was developed as an engineering and research project exploring the application of AI on edge hardware.

The documentation describes the project's architecture, research direction, and intended capabilities. It does not represent a currently operational military system or production-ready autonomous platform.

---

## Authors

SANI was collaboratively developed by:

### Aman Sinha

AI, Edge AI, system architecture, embedded systems, and project development.

[GitHub](https://github.com/EzioAman) · [LinkedIn](https://www.linkedin.com/in/morfit2409/)

### Saumya Suman

AI/software development and project development.

[GitHub](https://github.com/saumyaaa78) · [SANI Repository](https://github.com/saumyaaa78/SANI)
