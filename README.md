# BitTrickle - Peer-to-Peer File Sharing System

## 📌 Goal and Learning Objectives

This project implements **BitTrickle**, a **permissioned peer-to-peer (P2P) file sharing system** with a **centralized indexing server**. The system is designed using both **client-server** and **peer-to-peer** architectures, with the following key components:

- **Server**: 
  - Authenticates users joining the P2P network.
  - Maintains an index of available files and their associated clients.
  - Supports file search requests and assists clients in connecting to each other.

- **Client**:
  - A command-line interface (CLI) application.
  - Allows users to:
    - Join the P2P network.
    - Share files with other users.
    - Search for and retrieve files from the network.

All **client-server communication** is handled over **UDP**, while **peer-to-peer (client-to-client)** file transfers occur over **TCP**.


