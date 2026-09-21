# Terraform (not implemented)

Out of scope for this challenge: no cloud infrastructure is provisioned.
This directory documents how it *would* be structured if this project grew
into a real cloud deployment, so the shape is obvious without writing
modules that would never be applied.

## Intended structure

```text
infrastructure/terraform/
├── main.tf              # provider config, backend state (e.g. S3 + DynamoDB lock)
├── variables.tf
├── outputs.tf
└── modules/
    ├── network/          # VPC, subnets, security groups
    ├── database/         # managed Postgres (RDS/Cloud SQL)
    ├── registry/         # container registry (ECR/GCR)
    └── cluster/          # Kubernetes cluster (EKS/GKE) running the
                           # manifests in ../kubernetes
```

## Why Terraform wasn't implemented here

The acceptance criteria for this challenge explicitly scope out a real
cloud deployment. Writing Terraform against no real cloud account would
either be unverifiable boilerplate or require provisioning real
infrastructure with no purpose — both work against the project's own
"don't build more than the task needs" principle (see
`docs/decisions.md`).
