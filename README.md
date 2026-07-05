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

### 🚧 In Progress

- Async task management
- Graceful shutdown
- HL7 message framing
- HL7 parser
- Structured logging
- Unit and integration tests

## Current Sprint

The current development sprint is focused on implementing explicit asyncio task management to support background session execution and prepare the server for graceful shutdown.