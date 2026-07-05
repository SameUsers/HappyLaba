# HL7 Analyzer Server (Production)

This repository contains the production architecture of the HL7 Analyzer Server.
The project is focused on building a reliable, asynchronous HL7 TCP server with a clean, extensible architecture suitable for production deployments.

## Features

### ✅ Implemented

- Asynchronous TCP server built on asyncio
- Session lifecycle management
- UUID-based session registry
- Connection validation
- Transport-level exception handling
- Clean layered architecture
- Dependency injection via AppBuilder
- Configurable server and session settings
- Async task management
- Structured logging
- Graceful shutdown

### 🚧 In Progress

- HL7 message framing
- HL7 parser
- Unit and integration tests

## Current Sprint

The current sprint focuses on HL7 message framing.