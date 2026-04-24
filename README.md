
#  CI/CD Pipeline with Security Checks

This project is a simple implementation of a CI/CD pipeline where security checks are added at different stages to catch issues early.

--

##  What I did

The goal was to build a pipeline that doesn’t just build the app, but also checks for security problems before moving forward.

I added the following:
SAST (code scanning) using a tool like SonarQube/Snyk to find issues in the code
Secret scanning using Gitleaks / TruffleHog to make sure no API keys or passwords are committed
Container scanning** using Trivy to check the Docker image for known vulnerabilities

---

##  How the pipeline works

```text
Push code → Scan code → Check secrets → Build Docker image → Scan image
```

Each step runs automatically using GitHub Actions.

---

##  Security rule (Kill Switch)

One important part of this pipeline is that it **fails the build if serious vulnerabilities are found**.

This is done using:

```bash
trivy image --severity HIGH,CRITICAL --exit-code 1 my-app
```

So if there are HIGH or CRITICAL issues, the pipeline stops immediately.

---

##  Current status

Right now, the pipeline fails at the image scanning step.

This is because of some vulnerabilities in the base Docker image (Debian packages like ncurses/systemd), not because of the application code.

I kept it this way on purpose to show that the security gate is actually working.

---

##  Tools used

* GitHub Actions
* Docker
* Trivy
* Gitleaks / TruffleHog
* SonarQube / Snyk (for SAST)

---

##  What I’d improve next

* Use a smaller/secure base image (like slim or alpine)
* Reduce OS-level vulnerabilities
* Improve scan speed

---

## 🔗 Repo

[https://github.com/adityakaldate21-dev/Bharat-mail](https://github.com/adityakaldate21-dev/Bharat-mail)

---

##  Final note

The pipeline is doing what it’s supposed to do — it blocks builds when high-risk vulnerabilities are present.


