# QR Label Generator & Database Integration Tool

**Desktop Application | Python, PySide6, Multiple Database Types**

Universal QR code generation and label printing system for warehouse and logistics operations, designed to integrate with both legacy and modern database environments without impacting production data.

## Overview
This application connects to existing enterprise databases, extracts product records in read-only mode, generates unique QR codes, and produces printable PDF labels for industrial use. It was built to operate safely against aging infrastructure while remaining compatible with modern systems.

## Features Implemented
- Flexible database connection system supporting:
  - MS SQL Server (2012–2014)
  - MySQL
  - SQLite
- Intelligent column mapping with automatic fallback logic for inconsistent database schemas
- QR tracking system with cross-reference logic to identify products missing QR codes
- Strict read-only data access to guarantee zero impact on client production databases
- PDF label generation system aligned with industrial printing requirements

## Key Achievement
Successfully integrated with 10+ year old legacy databases without requiring any schema changes.

## Tech Stack
Python, PySide6, SQLite, PyODBC, WeasyPrint, Pillow
