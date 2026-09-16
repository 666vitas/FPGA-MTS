# Security and Hardware Safety Policy

FPGA-MTS is a research-stage control system that can affect real laboratory hardware. Security reports and hardware-safety reports are therefore treated as part of the same responsible-disclosure process when a software or FPGA defect could cause unsafe output behavior.

## Supported scope

The actively maintained scope is the current `main` branch and the current gate documented in `docs/CURRENT_STATUS.md`.

Historical experiment folders, archived builds, copied upstream/reference projects under `reference/`, and old bitstreams are retained for traceability and are not automatically supported releases.

## What to report

Please report issues such as:

- authentication, command-execution, or remote-control vulnerabilities in the Host path;
- unsafe register or state transitions that could bypass `SAFE` behavior;
- output-range, saturation, polarity, or readback defects that could create hazardous hardware behavior;
- dependency or build-chain vulnerabilities that affect a supported workflow;
- accidental disclosure of credentials, tokens, private keys, or sensitive laboratory data.

Ordinary functional bugs that do not involve security or hazardous hardware behavior can be reported as normal GitHub issues.

## Responsible disclosure

Do **not** publish exploit details, credentials, or instructions for reproducing hazardous output behavior in a public issue.

If GitHub Private Vulnerability Reporting is enabled for this repository, use **Security → Report a vulnerability**. If that option is not available, open a minimal public issue titled `[security] request private contact channel` without sensitive technical details so the maintainer can arrange a private channel.

## Hardware safety boundary

Before any real-hardware test, the current gate and readback requirements take precedence over convenience or automation. In particular:

- do not parallel FPGA `OUT2` with another active output;
- do not route `OUT2` to a laser current-modulation input unless a future gate explicitly authorizes that architecture;
- do not automatically increase feedback gain, widen voltage/range limits, invert polarity, or relock after a fault;
- identity, communication, readback, saturation, clipping, or range anomalies must return the experiment to `SAFE`;
- software tests, RTL simulation, and timing reports are not substitutes for physical hardware validation.

The authoritative current hardware state and known limitations are recorded in `docs/CURRENT_STATUS.md`.

## Disclosure expectations

The maintainer will acknowledge reproducible reports when possible, separate confirmed facts from unverified hypotheses, and avoid describing a fix as hardware-validated until the corresponding hardware gate has actually been completed.