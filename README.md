# THE EMPTY DASHBOARD: FALSE POSITIVE

## Challenge Information

- Name: The Empty Dashboard: False Positive
- Category: Web
- Difficulty: Hard+
- Expected Solve Time: 30–60 minutes
- Flag Format: CTF{...}

## Story

A routine security audit has flagged an internal analytics portal as operational, but the dashboard is showing almost nothing.

The system belongs to an old telemetry environment that was partially decommissioned. Most of its backend services are no longer maintained, yet the portal is still responding to authenticated users.

You have been given access to a limited analyst account.

Something about the application does not behave the way it should.

Some information appears inconsistent.

Some parts of the system respond differently depending on how a request is made.

The application claims certain operations are restricted, but the underlying system may not agree.

Your task is to investigate the portal, understand its behavior, and recover the hidden incident data.

### Your Objective

1. Investigate the analytics dashboard.
2. Examine how the application processes requests.
3. Identify inconsistencies in the application's behavior.
4. Follow the available evidence through the system.
5. Recover the final incident report and obtain the flag.


## Access Credentials

**Username:**
```
analyst
```

**Password:**
```
analyst2026
```

These are provided challenge credentials and are not intended to be discovered or bypassed.

## Installation & Setup

Ensure Python 3.9+ is installed.

1. Clone the repository and enter the challenge directory:
```bash
cd empty-dashboard
```

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Windows activation:
```cmd
venv\Scripts\activate
```

4. Linux/macOS activation:
```bash
source venv/bin/activate
```

5. Install dependencies:
```bash
pip install -r requirements.txt
```

6. Copy `.env.example` to `.env` and configure the required values:
```bash
cp .env.example .env
```

7. Launch:
```bash
python run.py
```

## Starting URL

http://localhost:5000/

## Rules

- The challenge is intended to be solved through the web application.
- Source-code inspection is not required for the intended solve.
- LLMs and AI assistants are allowed.
- Automated requests and normal web-security testing tools are allowed where permitted by the competition.
- Do not attack infrastructure outside the challenge environment.

Good luck.

The dashboard is empty.  
The system isn't.
