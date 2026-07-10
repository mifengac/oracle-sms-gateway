# Oracle SMS Gateway Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an internal HTTP SMS gateway that writes messages into the Oracle `yfgadb.dfsdl` table so business projects no longer need their own Oracle 11g client.

**Architecture:** Business projects call one FastAPI service. The service validates payloads, fills fixed Oracle SMS fields from `.env`, checks recent duplicates by `eid + mobile`, then inserts rows into Oracle. Oracle Instant Client lives inside this project locally but is ignored by Git.

**Tech Stack:** Python 3.10+, FastAPI, uvicorn, python-oracledb thick mode, standard-library unit tests.

## Global Constraints

- Project directory: `/home/longshao/project/oracle-sms-gateway`
- Project name: `oracle-sms-gateway`
- Oracle DSN default: `10.45.100.147:1521/yfgxpt`
- Oracle SMS table: `yfgadb.dfsdl`
- Oracle SMS sequence: `yfgadb.seq_sendsms`
- Default SMS `USERPORT`: `0006`
- The local `.env` file and `instantclient_11_2/` must not be committed to Git.
- Do not perform repository-level Git operations in `/home/longshao/project`.

---

### Task 1: Core Validation And Send Logic

**Files:**
- Create: `app/config.py`
- Create: `app/models.py`
- Create: `app/schemas.py`
- Create: `app/sms_service.py`
- Test: `tests/test_core.py`

**Interfaces:**
- Produces: `Settings.from_mapping(mapping) -> Settings`
- Produces: `parse_send_payload(payload, settings) -> SendRequest`
- Produces: `SmsService.send_rows(rows, dedup_hours) -> SmsSendResult`

- [ ] **Step 1: Write failing tests**
- [ ] **Step 2: Run `python3 -m unittest discover -s tests -v` and confirm imports fail**
- [ ] **Step 3: Implement minimal core modules**
- [ ] **Step 4: Run unit tests and confirm they pass**

### Task 2: Oracle Repository

**Files:**
- Create: `app/oracle_repo.py`
- Test: `tests/test_oracle_repo.py`

**Interfaces:**
- Consumes: `Settings`
- Consumes: `SmsInsertRow`
- Produces: `OracleSmsRepository.last_deadtime(eid, mobile)`
- Produces: `OracleSmsRepository.insert_sms(row)`
- Produces: `OracleSmsRepository.ping()`

- [ ] **Step 1: Write SQL construction tests without connecting to Oracle**
- [ ] **Step 2: Run tests and confirm repository is missing**
- [ ] **Step 3: Implement repository with lazy `oracledb` import**
- [ ] **Step 4: Run unit tests and confirm they pass**

### Task 3: HTTP API

**Files:**
- Create: `app/main.py`

**Interfaces:**
- Consumes: `parse_send_payload`
- Consumes: `SmsService`
- Produces: `GET /health`
- Produces: `GET /ready`
- Produces: `POST /api/v1/sms/send`

- [ ] **Step 1: Implement FastAPI routes**
- [ ] **Step 2: Ensure API token is checked when configured**
- [ ] **Step 3: Keep Oracle connection lazy so tests and imports do not require Oracle**

### Task 4: Deployment Files And Local Client

**Files:**
- Create: `.gitignore`
- Create: `.env`
- Create: `.env.example`
- Create: `requirements.txt`
- Create: `README.md`
- Create: `systemd/oracle-sms-gateway.service`
- Move: `/home/longshao/project/instantclient_11_2` to `/home/longshao/project/oracle-sms-gateway/instantclient_11_2`

**Interfaces:**
- Produces: clear offline deployment instructions
- Produces: local `.env` with Oracle and SMS settings

- [ ] **Step 1: Create ignored local config and example config**
- [ ] **Step 2: Create requirements and systemd service**
- [ ] **Step 3: Move Oracle Instant Client into project directory**
- [ ] **Step 4: Run final verification commands**
