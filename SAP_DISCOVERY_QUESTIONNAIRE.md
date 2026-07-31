# 🏗️ SAP SaaS Application Discovery Questionnaire — AWS Migration

> Pre-migration discovery for 300+ SAP SaaS applications aligned with AWS Well-Architected Framework (SAP Lens)

**Purpose:** Systematic discovery to understand current state, dependencies, and target architecture before migrating SAP SaaS applications to AWS.

**Scope:** 300+ applications | Current state unknown | Hosting unknown

---

## 📋 How to Use This Document

1. **Phase 1:** Application Portfolio Discovery (Section 1-2) — Identify what exists
2. **Phase 2:** Technical Deep-Dive (Section 3-6) — Understand each app's characteristics
3. **Phase 3:** Migration Readiness (Section 7-8) — Determine migration strategy per app
4. **Phase 4:** Well-Architected Assessment (Section 9) — Design target state on AWS

For 300+ apps, start with a **high-level inventory sweep** (Section 1), then deep-dive on critical apps first.

---

## 1. Application Portfolio Inventory (Per Application)

### 1.1 Basic Identity

| # | Question | Why It Matters |
|---|----------|---------------|
| 1 | What is the application name and version? | Baseline identification |
| 2 | Who is the application owner / business sponsor? | Accountability for migration decisions |
| 3 | What business function does it serve? (Finance, HR, Supply Chain, CRM, etc.) | Priority and criticality assessment |
| 4 | Is this a SAP standard product (S/4HANA, ECC, BW, CRM, SRM, SCM, PI/PO) or custom-built on SAP platform? | Determines migration approach |
| 5 | What is the SAP product version and support pack level? | Compatibility with AWS certified instances |
| 6 | Is this a SaaS application you subscribe to, or self-hosted SAP? | Fundamental architecture decision |
| 7 | Who is the current SaaS provider / hosting partner? | Contractual and data portability assessment |
| 8 | What is the contract end date / renewal date? | Migration timeline driver |
| 9 | Is this application in active use, maintenance mode, or decommission candidate? | Portfolio rationalization |
| 10 | How many active users? (Named users, concurrent users) | Sizing and licensing |

### 1.2 Classification & Priority

| # | Question | Why It Matters |
|---|----------|---------------|
| 11 | Business criticality: Mission Critical / Business Critical / Business Operational / Office Productivity? | Migration wave planning |
| 12 | What is the RTO (Recovery Time Objective)? | DR architecture design |
| 13 | What is the RPO (Recovery Point Objective)? | Backup strategy |
| 14 | Is there a compliance requirement? (SOX, GDPR, HIPAA, GxP, PCI-DSS) | Security controls and region selection |
| 15 | What happens if this application is down for 4 hours? 24 hours? 1 week? | True criticality validation |

---

## 2. Current Hosting & Infrastructure

### 2.1 Where Does It Live Today?

| # | Question | Why It Matters |
|---|----------|---------------|
| 16 | Where is the application currently hosted? (On-premises DC / Colo / Private Cloud / Other Public Cloud / SaaS provider managed) | Migration source identification |
| 17 | If on-premises: which data center, location, rack? | Network connectivity planning |
| 18 | If cloud-hosted: which provider, region, account? | Direct migration vs re-platform |
| 19 | What is the current OS? (SLES, RHEL, Windows, AIX) | OS compatibility on AWS |
| 20 | What is the database? (HANA, Oracle, DB2, SQL Server, MaxDB, Sybase ASE) | Database migration strategy |
| 21 | Database version and size (data + logs + backup)? | Instance sizing and storage |
| 22 | Is the application running on physical or virtual infrastructure? (VMware, Hyper-V, bare metal) | Migration tooling selection |
| 23 | CPU cores / RAM / Storage allocated vs. actually used? | Right-sizing on AWS |
| 24 | What is the SAPS rating of current hardware? | AWS instance selection (certified SAPS) |

### 2.2 Landscape Architecture

| # | Question | Why It Matters |
|---|----------|---------------|
| 25 | What environments exist? (Dev / QA / Pre-Prod / Prod / Sandbox / Training) | Total footprint and cost |
| 26 | Is this a 3-tier landscape (DEV → QAS → PRD)? | Transport management and CI/CD |
| 27 | Is there a Disaster Recovery (DR) environment? Where? | DR design on AWS |
| 28 | Are environments in the same location or distributed? | Network topology |
| 29 | What is the system SID for each environment? | SAP system identification |

---

## 3. Application Architecture & Dependencies

### 3.1 Integration & Interfaces

| # | Question | Why It Matters |
|---|----------|---------------|
| 30 | What other SAP systems does this application integrate with? | Migration wave dependency |
| 31 | What non-SAP systems does it integrate with? (CRM, EDI, banks, 3rd party) | Interface redesign needs |
| 32 | What middleware is used? (SAP PI/PO, CPI, MuleSoft, BizTalk, custom) | Integration layer migration |
| 33 | How are integrations implemented? (RFC, IDoc, BAPI, REST API, SOAP, file-based, DB links) | Protocol compatibility |
| 34 | What is the data flow direction? (Inbound / Outbound / Bidirectional) | Testing sequence planning |
| 35 | Frequency of data exchange? (Real-time / Near-real-time / Batch hourly/daily) | Latency requirements |
| 36 | Are there any on-premises systems that MUST remain on-premises? | Hybrid connectivity design |
| 37 | What are the network latency requirements between systems? (<1ms, <10ms, <100ms) | Placement and region selection |

### 3.2 Data Characteristics

| # | Question | Why It Matters |
|---|----------|---------------|
| 38 | Total data volume (DB size, file storage, archive)? | Storage and transfer planning |
| 39 | Data growth rate per month/year? | Capacity planning |
| 40 | Is there data archiving in place? (SAP ILM, ADK, custom) | Pre-migration cleanup opportunity |
| 41 | What is the data residency requirement? (Country, region) | AWS region selection |
| 42 | Is there sensitive/classified data? (PII, PHI, financial, trade secrets) | Encryption and access controls |
| 43 | What is the data retention policy? | Storage tier selection |

---

## 4. Operational Excellence (Well-Architected Pillar 1)

### 4.1 Operations & Management

| # | Question | Why It Matters |
|---|----------|---------------|
| 44 | Who manages this application today? (Internal team / MSP / SaaS provider) | Operations model on AWS |
| 45 | What monitoring tools are in place? (Solution Manager, Nagios, PRTG, Dynatrace, custom) | AWS monitoring strategy |
| 46 | How are changes deployed? (Transport Management, CI/CD, manual) | DevOps maturity assessment |
| 47 | What is the patching cadence? (Monthly, quarterly, yearly, never) | Patch management on AWS |
| 48 | How are incidents managed? (ITSM tool, process, SLAs) | Operational runbook design |
| 49 | What is the current uptime SLA? | AWS architecture target |
| 50 | How are backups performed today? (Schedule, tool, retention, tested?) | AWS Backup strategy |
| 51 | When was the last successful DR test? | DR readiness validation |
| 52 | Are there any recurring operational issues? (Performance, crashes, space issues) | Fix before/during migration |
| 53 | What automation exists today? (Scripts, scheduled jobs, cron, SAP jobs) | Automation migration |
| 54 | Are there batch processing windows? (Nightly, month-end, year-end) | Performance window requirements |

### 4.2 Support & Knowledge

| # | Question | Why It Matters |
|---|----------|---------------|
| 55 | Is there documentation? (Architecture diagrams, runbooks, SOPs) | Knowledge gap assessment |
| 56 | Is the support team AWS-skilled? | Training needs |
| 57 | What SAP support level do you have? (Standard, Enterprise, Preferred Care) | SAP-AWS support alignment |
| 58 | Are there any SAP OSS notes or known issues affecting this system? | Pre-migration fixes |

---

## 5. Security (Well-Architected Pillar 2)

### 5.1 Identity & Access

| # | Question | Why It Matters |
|---|----------|---------------|
| 59 | How do users authenticate? (SAP GUI, Fiori, SSO, LDAP, SAML, certificates) | IAM design on AWS |
| 60 | Is Single Sign-On (SSO) configured? What IdP? (Azure AD, Okta, SAP IAS, ADFS) | SSO integration on AWS |
| 61 | How many user roles/authorization profiles exist? | Security complexity |
| 62 | Is there Privileged Access Management (PAM) for Basis/DBA accounts? | AWS privileged access strategy |
| 63 | Are there service accounts / RFC users? How are credentials managed? | Secrets management (AWS Secrets Manager) |
| 64 | Is SAP GRC Access Control in use? | Compliance automation |

### 5.2 Network Security

| # | Question | Why It Matters |
|---|----------|---------------|
| 65 | What network segmentation exists? (VLANs, firewalls, DMZ) | VPC design |
| 66 | What ports/protocols are required? (3200-3299, 8000-8099, 50000-50099, 443) | Security group rules |
| 67 | Is there a VPN or private connectivity to the current host? | AWS Direct Connect / VPN |
| 68 | Are there IP whitelisting requirements with partners/banks? | Elastic IP / NAT design |
| 69 | Is network traffic encrypted in transit? (SNC, TLS, IPSec) | Encryption requirements |

### 5.3 Data Security

| # | Question | Why It Matters |
|---|----------|---------------|
| 70 | Is data encrypted at rest? (HANA native, TDE, volume encryption) | AWS KMS / EBS encryption |
| 71 | Who manages encryption keys today? | KMS vs CloudHSM |
| 72 | Is there data masking for non-production environments? | Data anonymization strategy |
| 73 | Are security audits performed? (Frequency, last finding) | Compliance on AWS |
| 74 | Is SAP Security Audit Log enabled? | CloudTrail + SAP audit alignment |

---

## 6. Reliability (Well-Architected Pillar 3)

### 6.1 High Availability

| # | Question | Why It Matters |
|---|----------|---------------|
| 75 | Is High Availability (HA) configured today? How? | AWS HA architecture |
| 76 | For HANA: Is System Replication (HSR) configured? (Sync/Async, same site/cross-site) | Multi-AZ HANA design |
| 77 | For application layer: Is there clustering? (Pacemaker, SIOS, Windows Failover) | AWS clustering strategy |
| 78 | What is the actual achieved availability? (Uptime % last 12 months) | SLA baseline |
| 79 | What was the last unplanned outage? Root cause? Duration? | Reliability gaps |
| 80 | How long does a failover take today? | Target failover time on AWS |

### 6.2 Backup & Recovery

| # | Question | Why It Matters |
|---|----------|---------------|
| 81 | Backup tool and method? (HANA Backint, filesystem, storage snapshots, 3rd party) | AWS Backup + Backint for S3 |
| 82 | Backup schedule? (Full daily? Log every 15 min? Weekly full + daily incremental?) | Backup design |
| 83 | Backup retention? (30 days, 90 days, 7 years) | S3 lifecycle policy |
| 84 | Has a restore ever been tested? When? How long did it take? | Recovery confidence |
| 85 | Where are backups stored? (Local disk, tape, NFS, object storage) | S3 migration |

---

## 7. Performance Efficiency (Well-Architected Pillar 4)

### 7.1 Compute & Memory

| # | Question | Why It Matters |
|---|----------|---------------|
| 86 | Peak CPU utilization? (Average, P95, month-end) | Instance type selection |
| 87 | Peak memory utilization? (HANA resident memory, total allocated) | Memory-optimized instances |
| 88 | For HANA: What is the total memory footprint? (Data + row store + column store) | HANA certified instance sizing |
| 89 | Are there performance issues today? (Slow reports, long batch jobs, user complaints) | Performance baseline |
| 90 | SAPS requirement (from SAP sizing report or current hardware spec)? | AWS certified SAPS mapping |
| 91 | Is the workload CPU-bound or memory-bound? | Instance family selection |

### 7.2 Storage & I/O

| # | Question | Why It Matters |
|---|----------|---------------|
| 92 | Storage type currently used? (SAN, NAS, local SSD, all-flash) | EBS type selection (gp3, io2, io2 Block Express) |
| 93 | I/O requirements? (IOPS, throughput for data, log, backup volumes) | Storage performance design |
| 94 | For HANA: KPI compliance? (Data volume read < 400 MB/s, log write < 10ms) | AWS storage certification |
| 95 | Are there shared filesystems? (NFS for transports, sapmnt, interfaces) | EFS / FSx design |
| 96 | Total storage capacity required? (Data, logs, backups, shared) | Cost estimation |

### 7.3 Network Performance

| # | Question | Why It Matters |
|---|----------|---------------|
| 97 | Network bandwidth between app and DB tier? | Placement group / enhanced networking |
| 98 | Current latency between SAP tiers? | Single-AZ vs Multi-AZ for app layer |
| 99 | External bandwidth requirements? (User access, EDI, partner connections) | Direct Connect sizing |
| 100 | Geographic distribution of users? | CloudFront / Fiori Launchpad caching |

---

## 8. Cost Optimization (Well-Architected Pillar 5)

### 8.1 Current Costs

| # | Question | Why It Matters |
|---|----------|---------------|
| 101 | Current annual cost for this application? (Infra + license + support + operations) | TCO comparison |
| 102 | SAP license model? (Named users, engine, packages, BYOL) | License portability |
| 103 | Is there existing SAP on AWS BYOL eligibility? | Cost optimization |
| 104 | Current hosting contract value and remaining term? | Exit costs |
| 105 | Are Dev/QA environments running 24/7? | Shutdown scheduling opportunity |
| 106 | Is there over-provisioned capacity? | Right-sizing savings |

### 8.2 Target Cost Model

| # | Question | Why It Matters |
|---|----------|---------------|
| 107 | Budget for AWS migration (one-time)? | Migration approach selection |
| 108 | Budget for AWS run (monthly/annual)? | Target architecture constraints |
| 109 | Willingness to commit? (1-year, 3-year Reserved Instances / Savings Plans) | Pricing optimization |
| 110 | Interest in managed services? (AWS managed SAP, partner managed) | OpEx model |

---

## 9. Sustainability (Well-Architected Pillar 6)

| # | Question | Why It Matters |
|---|----------|---------------|
| 111 | Is there a sustainability / carbon reduction goal? | Graviton instance consideration |
| 112 | Can non-HANA workloads run on ARM/Graviton? | Cost + sustainability benefit |
| 113 | Are there idle/zombie systems that can be decommissioned? | Portfolio cleanup |
| 114 | Can systems be consolidated? (Multiple SIDs → single S/4HANA) | Simplification |

---

## 10. Migration Strategy Assessment

### 10.1 The 7 R's (Per Application)

| # | Question | Purpose |
|---|----------|---------|
| 115 | Can this application be **Retired**? (No longer needed) | Portfolio reduction |
| 116 | Can this application be **Retained**? (Stay as-is for now) | Phase planning |
| 117 | Can this application be **Rehosted** (lift-and-shift)? | Fastest migration |
| 118 | Can this application be **Replatformed**? (Lift-shift-optimize: e.g., Oracle → HANA) | Partial modernization |
| 119 | Can this application be **Refactored**? (e.g., ECC → S/4HANA conversion) | Full modernization |
| 120 | Can this application be **Repurchased**? (Move to SaaS: SAP BTP, SuccessFactors, Ariba) | SaaS alternative |
| 121 | Can this application be **Relocated**? (VMware Cloud on AWS) | Quick migration path |

### 10.2 Migration Complexity

| # | Question | Purpose |
|---|----------|---------|
| 122 | How many custom objects? (Z-programs, enhancements, custom tables) | Complexity and testing effort |
| 123 | How many interfaces? | Integration testing scope |
| 124 | What is the acceptable downtime window for cutover? | Migration method selection |
| 125 | Are there any technical blockers? (Unsupported OS, EOL DB, legacy hardware dependencies) | Blocker resolution |
| 126 | What testing resources are available? (Functional testers, automation, UAT team) | Testing planning |
| 127 | Is there an SAP Readiness Check available? | Compatibility validation |
| 128 | Has SAP HANA Hardware & Cloud Measurement Tool (HCMT) been run? | Sizing validation |

---

## 11. Discovery Tools Recommended

| Tool | Purpose | When to Use |
|------|---------|-------------|
| **AWS Application Discovery Service** | Auto-discover servers, dependencies, utilization | Phase 1 — inventory |
| **AWS Migration Hub** | Track migration progress across 300+ apps | Throughout |
| **SAP EarlyWatch Alert** | SAP system health and performance baseline | Phase 2 — deep-dive |
| **SAP Readiness Check** | Validate S/4HANA conversion readiness | If refactoring |
| **HANA HCMT** | Storage and compute sizing | Sizing validation |
| **AWS Migration Evaluator** | TCO analysis and right-sizing | Cost modeling |
| **SAP Landscape Management (LaMa)** | Landscape topology discovery | Complex landscapes |
| **CloudEndure / AWS MGN** | Replication-based migration (rehost) | Lift-and-shift |

---

## 12. Deliverables After Discovery

| # | Deliverable | Contains |
|---|-------------|----------|
| 1 | **Application Inventory Matrix** | All 300+ apps with classification, priority, owner |
| 2 | **Dependency Map** | Integration flows between all systems |
| 3 | **Migration Wave Plan** | Grouped applications by dependency and priority |
| 4 | **Target Architecture (per wave)** | AWS VPC, instance types, storage, HA/DR design |
| 5 | **Sizing Report** | SAPS mapping to AWS instances, storage IOPS |
| 6 | **Cost Estimate** | Monthly AWS cost per app + total TCO comparison |
| 7 | **Risk Register** | Blockers, dependencies, compliance gaps |
| 8 | **Migration Runbook (per app)** | Step-by-step cutover procedures |

---

## 13. Quick-Start: Priority Categorization Template

Use this to quickly categorize all 300+ apps before deep-dive:

```
| App Name | Owner | Type | Criticality | Users | DB Size | Strategy | Wave |
|----------|-------|------|-------------|-------|---------|----------|------|
| ECC Prod | Finance | ERP | Mission Critical | 500 | 2 TB | Replatform | 3 |
| BW Prod | Analytics | DW | Business Critical | 100 | 5 TB | Rehost | 2 |
| SRM Dev | Procurement | SRM | Office | 10 | 50 GB | Retire | 1 |
| CRM Prod | Sales | CRM | Business Critical | 200 | 500 GB | Repurchase (C4C) | 4 |
| PI/PO | Integration | Middleware | Mission Critical | N/A | 100 GB | Replatform (CPI) | 2 |
```

---

## References

- [AWS Well-Architected Framework — SAP Lens](https://docs.aws.amazon.com/wellarchitected/latest/sap-lens/sap-lens.html)
- [AWS SAP on AWS](https://aws.amazon.com/sap/)
- [SAP on AWS Technical Documentation](https://docs.aws.amazon.com/sap/latest/general/welcome.html)
- [AWS Migration Hub](https://aws.amazon.com/migration-hub/)
- [AWS Application Discovery Service](https://aws.amazon.com/application-discovery/)
- [SAP HANA on AWS — Certified Instances](https://aws.amazon.com/sap/solutions/saphana/)
- [AWS Backint Agent for SAP HANA](https://docs.aws.amazon.com/sap/latest/sap-hana/aws-backint-agent-for-sap-hana.html)

---

**Total Questions:** 128 structured discovery questions across 13 sections, aligned with 6 AWS Well-Architected pillars + SAP-specific migration best practices.

**Recommended approach for 300+ apps:**
1. Week 1-2: Automated discovery (AWS ADS) + portfolio spreadsheet (Section 1, 13)
2. Week 3-4: Deep-dive on top 20 critical apps (Sections 2-9)
3. Week 5-6: Migration strategy assignment + wave planning (Section 10)
4. Week 7-8: Target architecture + cost modeling (Section 11-12)
